#!/usr/bin/env python3
"""This would be a game source for MAME software… but I haven't actually finished it yet
TODO: Actually put this in game_sources, once we are more comfy this works nicely as per below todos etc, mainly the first two
TODO: Each platform should be an option; maybe something like there's a list config item for "use these software platforms" and then anything in there which is the name of something in software_list_platforms is used for anything specific, and anything else it just launches the software with machine name = software name, or tries to and skips if something fails
TODO: Don't blow up if MAME's not installed or anything like that
TODO: Platform-specific metadata (e.g. specify Neo Geo = SaveType.MemoryCard); may want to refactor platform_metadata so it can work with this (for now though I only care about Neo Geo and such, which isn't in there anyway). Neo Geo in particular could get things like genre, icon from the arcade stuff, because it will always be equivalent to an arcade game, unless it isn't"""
import logging
from collections.abc import Collection, Mapping, Sequence

from meowlauncher.common_types import MediaType
from meowlauncher.exceptions import EmulationNotSupportedError
from meowlauncher.games.common.emulator_command_line_helpers import mame_base
from meowlauncher.games.mame_common.software_list import Software, get_software_list_by_name
from meowlauncher.info import GameInfo
from meowlauncher.launch_command import LaunchCommand
from meowlauncher.output.desktop_files import make_launcher
from meowlauncher.util.region_info import TVSystem

logger = logging.getLogger(__name__)


class SoftwareListPlatform:
	def __init__(
		self, name: str, lists: Mapping[MediaType, Collection['str']], launch_params_function
	) -> None:
		self.name = name
		self.lists = lists
		self.launch_params_function = launch_params_function

	def get_launch_command(self, software):
		return self.launch_params_function(software)


def _launch_with_software(system_name: str, software: 'SoftwareLauncher') -> Sequence[str]:
	# Use fully qualified id with : here to avoid ambiguity
	return mame_base(system_name, software=software.id)


def _quizwiz(software: 'SoftwareLauncher'):
	return _launch_with_software('quizwizc', software)


def _neo_geo(software: 'SoftwareLauncher'):
	compat = software.software.compatibility
	if compat and 'AES' not in compat:
		raise EmulationNotSupportedError('Not compatible with AES')
	return _launch_with_software('aes', software)


def _super_cassette_vision(software: 'SoftwareLauncher'):
	machine = 'scv_pal' if software.info.specific_info.get('TV Type') == TVSystem.PAL else 'scv'
	return _launch_with_software(machine, software)


software_list_platforms = {
	# For simplicity we're just going to only use certain lists at the moment, I'm very sorry
	# TODO: Will also need required_romset, and do -verifyroms on that to see that it's launchable; e.g. no point doing Neo Geo if -verifyroms aes fails, maybe like a main_driver so we get our CPU/screen/etc info from there, and we can skip it if broken and if main_config.exclude_non_working and machine.emulation_status == EmulationStatus.Broken and machine.basename not in main_config.non_working_whitelist: skip
	SoftwareListPlatform('Coleco Quiz Wiz', {MediaType.Cartridge: {'quizwiz'}}, _quizwiz),
	SoftwareListPlatform('Neo Geo', {MediaType.Cartridge: {'neogeo'}}, _neo_geo),
	SoftwareListPlatform(
		'Super Cassette Vision', {MediaType.Cartridge: {'scv'}}, _super_cassette_vision
	),
	# jakks stuff (set these up all as platform = Plug & Play)
	# vii (maybe this should be platform = Plug & Play? Or just "Vii")
	# nes
	# nes_ntbrom
	# ekara stuff
	# icanguit
	# icanpian
	# microvision
	# entex_sag
	# vic1001_cart
	# Not working:
	# rx78 (albeit kinda works)
	# tvgogo
	# c65
	# n64dd
}


class SoftwareLauncher:
	def __init__(self, software: Software, platform: SoftwareListPlatform, media_type: MediaType):
		self.software = software
		self.platform = platform
		self.media_type = media_type

		self.info = GameInfo()

	@property
	def id(self):
		return f'{self.software.software_list.name}:{self.software.name}'

	def make_launcher(self) -> None:
		# if main_config.skip_mame_non_working_software:
		# if self.metadata.specific_info.get('MAME Emulation Status', EmulationStatus.Unknown) == EmulationStatus.Broken:
		# raise EmulationNotSupportedException('Not supported')
		# TODO Have option to skip if not working
		assert default_mame_executable, 'Would be checked by now'

		launch_params = LaunchCommand(
			default_mame_executable.executable, self.platform.get_launch_command(self)
		)

		make_launcher(launch_params, self.software.description, self.info, 'MAME software', self.id)


def add_software_metadata(software: SoftwareLauncher) -> None:
	"""TODO: Info:
	categories (but how?)
	languages (detect from regions)
	save_type
	input_info
	regions (from filename tags)
	Is notes automatic from software?
	disc_number, disc_total: From part stuff
	tv_type: From region/tags"""
	software.info.emulator_name = 'MAME'  # Will probably always be the case

	software.info.platform = software.platform.name
	software.info.media_type = software.media_type

	software.software.add_standard_info(software.info)


def add_software(software: SoftwareLauncher) -> None:
	add_software_metadata(software)

	# TODO: main_config.use_mame_arcade_icons and such

	try:
		software.make_launcher()
	except EmulationNotSupportedError:
		logger.exception('Could not launch %s', software.id)


def add_software_list_platform(platform: SoftwareListPlatform) -> None:
	if not default_mame_executable:
		logger.error('nope cannot do that')
		return
	for media_type, lists in platform.lists.items():
		for list_name in lists:
			software_list = get_software_list_by_name(list_name)
			if not software_list:
				continue
			for software_item in software_list.iter_available_software(default_mame_executable):
				software = SoftwareLauncher(software_item, platform, media_type)
				add_software(software)


def add_mame_software() -> None:
	for platform in software_list_platforms:
		add_software_list_platform(platform)
