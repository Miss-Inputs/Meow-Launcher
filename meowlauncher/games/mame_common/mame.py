import copy
import logging
import re
import subprocess
from collections.abc import Iterator, Mapping, Sequence
from functools import cached_property
from pathlib import Path, PurePath
from typing import cast
from xml.etree import ElementTree

from meowlauncher.common_paths import cache_dir
from meowlauncher.emulator import BaseEmulatorConfig, Emulator
from meowlauncher.game import Game
from meowlauncher.games.mame.mame_game import ArcadeGame
from meowlauncher.games.mame.mame_inbuilt_game import MAMEInbuiltGame
from meowlauncher.launch_command import LaunchCommand, rom_path_argument

logger = logging.getLogger(__name__)

# TODO: Potentially we want these methods to take a different path, or maybe Runner just needs an option to use a different config, etc


class MachineNotFoundError(Exception):
	"""This shouldn't be seen by the end user, ideally not actually thrown so maybe asserts are a better idea"""


class MAMENotInstalledError(Exception):
	"""Not having MAME installed is a normal thing, even if suboptimal. So remember to always catch this one! Well, mostly a reminder to myself to actually test for that case"""


class MAMEConfig(BaseEmulatorConfig):
	@classmethod
	def section(cls) -> str:
		return 'MAME'

	@classmethod
	def prefix(cls) -> str:
		return 'mame'

	use_xml_disk_cache: bool = True
	"""Store machine XML files on disk
	Maybe there are some scenarios where you might get better performance with it off (slow home directory storage, or just particularly fast MAME -listxml)
	Maybe it turns out _I'm_ the weird one for this being beneficial in my use case, and it shouldn't default to true? I dunno lol"""


def _get_autoboot_script_by_name(name: str) -> Path:
	# Hmm I'm not sure I like this one but whaddya do otherwise… where's otherwise a good place to store shit
	mame_common = Path(__file__).parent
	games_package = mame_common.parent
	meowlauncher_package = games_package.parent
	return meowlauncher_package / 'data' / 'mame_autoboot' / (name + '.lua')


class MAME(Emulator[Game]):
	# We are generic with Game instead of ArcadeGame here, as it is more versatile than that
	@classmethod
	def exe_name(cls) -> str:
		return 'mame'

	@classmethod
	def config_class(cls) -> type[MAMEConfig]:
		return MAMEConfig

	def __init__(self) -> None:
		super().__init__()
		self.config: MAMEConfig  # TODO: Is there really just no way to type that over and over and over again?
		self._xml_cache_path = cache_dir / self.version

	@cached_property
	def version(self) -> str:
		"""Note that there is a -version option in (as of this time of writing, upcoming) MAME 0.211, but might as well just use this, because it works on older versions"""
		version_proc = subprocess.run(
			[self.exe_path, '-help'], stdout=subprocess.PIPE, text=True, check=True
		)
		return version_proc.stdout.splitlines()[0]

	def _real_iter_mame_entire_xml(self) -> Iterator[tuple[str, ElementTree.Element]]:
		if self.config.use_xml_disk_cache:
			logger.info(
				'New MAME version found: %s; creating XML; this may take a while the first time it is run',
				self.version,
			)
			self._xml_cache_path.mkdir(exist_ok=True, parents=True)

		with subprocess.Popen(
			[self.exe_path, '-listxml'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
		) as proc:
			# I'm doing what the documentation tells me to not do and effectively using proc.stdout.read
			if not proc.stdout:
				return
			try:
				for _, element in ElementTree.iterparse(proc.stdout):
					if element.tag == 'machine':
						my_copy = copy.copy(element)
						machine_name = element.attrib['name']

						if self.config.use_xml_disk_cache:
							self._xml_cache_path.joinpath(machine_name + '.xml').write_bytes(
								ElementTree.tostring(element)
							)
						yield machine_name, my_copy
						element.clear()
			except ElementTree.ParseError:
				# Hmm, this doesn't show us where the error really is
				logger.exception('baaagh XML error in listxml')
		if self.config.use_xml_disk_cache:
			# Guard against the -listxml process being interrupted and screwing up everything, by only manually specifying it is done when we say it is done… wait does this work if it's an iterator? I guess it must if this exists
			self._xml_cache_path.joinpath('is_done').touch()

	def _cached_iter_mame_entire_xml(self) -> Iterator[tuple[str, ElementTree.Element]]:
		for cached_file in self._xml_cache_path.iterdir():
			if cached_file.suffix != '.xml':
				continue
			driver_name = cached_file.stem
			yield driver_name, ElementTree.parse(cached_file).getroot()

	def iter_mame_entire_xml(self) -> Iterator[tuple[str, ElementTree.Element]]:
		if self.config.use_xml_disk_cache and self._xml_cache_path.joinpath('is_done').is_file():
			yield from self._cached_iter_mame_entire_xml()
		else:
			yield from self._real_iter_mame_entire_xml()

	def get_mame_xml(self, driver: str) -> ElementTree.Element:
		if self.config.use_xml_disk_cache:
			cache_file_path = self._xml_cache_path.joinpath(driver + '.xml')
			try:
				return ElementTree.parse(cache_file_path).getroot()
			except FileNotFoundError:
				pass

		try:
			proc = subprocess.run(
				[self.exe_path, '-listxml', driver],
				stdout=subprocess.PIPE,
				stderr=subprocess.DEVNULL,
				check=True,
			)
		except subprocess.CalledProcessError as cpe:
			raise MachineNotFoundError(driver) from cpe

		xml = ElementTree.fromstring(proc.stdout).find('machine')
		if not xml:
			raise MachineNotFoundError(
				driver
			)  # This shouldn't happen if -listxml didn't return success but eh
		return xml

	def listsource(self) -> Iterator[tuple[str, str]]:
		proc = subprocess.run(
			[self.exe_path, '-listsource'],
			stdout=subprocess.PIPE,
			stderr=subprocess.DEVNULL,
			text=True,
			check=True,
		)
		# Return code should always be 0 so if it's not I dunno what to do about that and let's just panic instead
		for line in proc.stdout.splitlines():
			# Machine names and source files both shouldn't contain spaces, so this should be fine
			line_split = line.split(maxsplit=2)
			assert len(line_split) == 2, '-listsource output only one column???!! what'
			yield cast(tuple[str, str], tuple(line_split))

	def verifysoftlist(self, software_list_name: str) -> Iterator[str]:
		# Unfortunately it seems we cannot verify an individual software, which would probably take less time
		proc = subprocess.run(
			[self.exe_path, '-verifysoftlist', software_list_name],
			text=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.DEVNULL,
			check=False,
		)
		# Don't check return code - it'll return 2 if one software in the list is bad

		software_verify_matcher = re.compile(
			rf'romset {software_list_name}:(.+) is (?:good|best available)$'
		)
		for line in proc.stdout.splitlines():
			# Bleh
			line_match = software_verify_matcher.match(line)
			if line_match:
				yield line_match[1]

	def verifyroms(self, basename: str) -> bool:
		try:
			# Note to self: Stop wasting time thinking you can make this faster
			subprocess.run(
				[self.exe_path, '-verifyroms', basename],
				stdout=subprocess.DEVNULL,
				stderr=subprocess.DEVNULL,
				check=True,
			)
		except subprocess.CalledProcessError:
			return False
		else:
			return True

	@classmethod
	def launch_args(
		cls,
		driver: str,
		slot: str | None = None,
		slot_options: Mapping[str, str] | None = None,
		*,
		has_keyboard: bool = False,
		autoboot_script: str | None = None,
		software: str | None = None,
		bios: str | None = None,
	) -> Sequence[str | PurePath]:
		args: list[str | PurePath] = ['-skip_gameinfo']
		if has_keyboard:
			args.append('-ui_active')

		if bios:
			args += ['-bios', bios]

		args.append(driver)
		if software:
			args.append(software)

		if slot_options:
			for name, value in slot_options.items():
				if not value:
					value = ''
				args += [f'-{name}', value]

		if slot:
			args += [f'-{slot}', rom_path_argument]

		if autoboot_script:
			args += ['-autoboot_script', _get_autoboot_script_by_name(autoboot_script)]

		return args

	def get_game_command(self, game: Game) -> 'LaunchCommand':
		# TODO: Launch ArcadeGame and MAMEInbuiltGame
		if isinstance(game, ArcadeGame):
			return LaunchCommand(self.exe_path, self.launch_args(game.machine.basename))
		if isinstance(game, MAMEInbuiltGame):
			return LaunchCommand(
				self.exe_path, self.launch_args(game.machine_name, bios=game.bios_name)
			)
		raise TypeError(f"Don't know how to launch {game}")

	# Other frontend commands: listfull, listclones, listbrothers, listcrc, listroms, listsamples, verifysamples, romident, listdevices, listslots, listmedia, listsoftware, verifysoftware, getsoftlist
