import contextlib
import re
import tempfile
from functools import cache
from pathlib import PurePath
from typing import TYPE_CHECKING

from meowlauncher.emulated_game import EmulatedGame
from meowlauncher.emulator_launcher import EmulatorLauncher
from meowlauncher.games.mame_common.software_list import (
	Software,
	SoftwareList,
	SoftwarePart,
	find_in_software_lists_with_custom_matcher,
	find_software_by_name,
	iter_software_lists_by_name,
)
from meowlauncher.launch_command import LaunchCommand
from meowlauncher.util.utils import find_filename_tags_at_end

from .rom import ROM, CompressedROM

if TYPE_CHECKING:
	from collections.abc import Collection

	from meowlauncher.config_types import PlatformConfig
	from meowlauncher.emulated_platform import StandardEmulatedPlatform
	from meowlauncher.emulator import LibretroCoreWithFrontend, StandardEmulator


def _software_list_product_code_matcher(part: 'SoftwarePart', product_code: str) -> bool:
	part_code = part.software.serial
	if not part_code:
		return False

	return product_code in part_code.split(', ')


@cache
def _software_lists_for_platform(
	platform: 'StandardEmulatedPlatform',
) -> 'Collection[SoftwareList]':
	return set(iter_software_lists_by_name(platform.software_list_names))


class ROMGame(EmulatedGame):
	def __init__(
		self, rom: ROM, platform: 'StandardEmulatedPlatform', platform_config: 'PlatformConfig'
	):
		super().__init__(platform_config)
		self.rom = rom
		self.info.platform = platform.name
		self.platform = platform
		self.filename_tags = find_filename_tags_at_end(rom.path.stem)

	def __str__(self) -> str:
		return self.name

	@property
	def name(self) -> str:
		# TODO: This should be better…
		name = self.rom.name
		if self.rom.ignore_name and self.info.names:
			name = self.info.names.get('Name', next(iter(self.info.names.values())))

		return name

	@property
	def related_software_lists(self) -> 'Collection[SoftwareList]':
		"""Returns software lists for this game's platform"""
		# TODO: I don't like this being here but 2600/C64/GB/Intellivision/NES needs it for now I guess
		return _software_lists_for_platform(self.platform)

	def get_software_list_entry(self) -> Software | None:
		if not self.platform.software_list_names:
			return None

		software_lists = self.related_software_lists
		software = None
		with contextlib.suppress(NotImplementedError):
			software = self.rom.get_software_list_entry(
				software_lists, self.platform.databases_are_byteswapped
			)
		if software:
			return software

		if (
			self.platform_config.options.get('find_software_by_product_code', False)
			and self.info.product_code
		):
			software = find_in_software_lists_with_custom_matcher(
				software_lists, _software_list_product_code_matcher, [self.info.product_code]
			)
			if software:
				return software

		if self.platform_config.options.get('find_software_by_name', False):
			software = find_software_by_name(software_lists, self.rom.name)
			if software:
				return software
		return None


class ROMLauncher(EmulatorLauncher):
	_clean_for_filename = re.compile(
		r'[^A-Za-z0-9_]'
	)  # You may notice that it doesn't even have spaces… just in case

	def __init__(
		self,
		game: ROMGame,
		emulator: 'StandardEmulator | LibretroCoreWithFrontend',
		platform_config: 'PlatformConfig',
	) -> None:
		self.game: ROMGame = game
		self.runner: 'StandardEmulator | LibretroCoreWithFrontend' = emulator
		super().__init__(game, emulator, platform_config.options)

	@property
	def game_id(self) -> str:
		return str(self.game.rom.path)

	def _make_very_safe_temp_filename(self) -> str:
		name = ROMLauncher._clean_for_filename.sub('-', self.name)
		name = name.lstrip('-')
		if not name:
			name = 'blank'
		return name

	@property
	def command(self) -> LaunchCommand:
		"""Returns an actual command that runs the game
		Uses 7z if necessary"""
		# TODO: Ideally EmulatorLauncher would do something useful with self.runner and then we call super() but that also needs refactoring
		# TODO: Add a check for self.game.rom.outer_extension being supported by 7zip, so we can add other formats to CompressedROM (zstd, etc)
		command = super().command
		if isinstance(
			self.game.rom, CompressedROM
		) and not self.runner.supports_compressed_extension(self.game.rom.outer_extension):
			temp_extraction_folder = PurePath(
				tempfile.gettempdir(), 'meow-launcher-' + self._make_very_safe_temp_filename()
			)
			extracted_path = temp_extraction_folder / self.game.rom.inner_filename
			command = command.replace_path_argument(extracted_path)
			command = command.prepend_command(
				LaunchCommand(
					PurePath('7z'), ['x', '-o' + str(temp_extraction_folder), self.game.rom.path]
				)
			)
			command = command.append_command(
				LaunchCommand(PurePath('rm'), ['-rf', temp_extraction_folder])
			)
		else:
			command = command.replace_path_argument(self.game.rom.path)
		return command
