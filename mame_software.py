#!/usr/bin/env python3
import datetime
import time

import launchers
from common_types import EmulationNotSupportedException, MediaType
from config import main_config
from info.emulator_command_lines import mame_base
from info.region_info import TVSystem
from metadata import EmulationStatus, Metadata
from software_list_info import get_software_list_by_name

#TODO: Actually call this from main (once below todos are resolved)
#TODO: Platform-specific metadata (e.g. specify Neo Geo = SaveType.MemoryCard); may want to refactor platform_metadata so it can work with this (for now though I only care about Neo Geo and such which isn't in there). Neo Geo in particular could get things like genre, icon from the arcade stuff, because it will always be equivalent to an arcade game, unless it isn't
#TODO: Each platform should be an option; maybe something like there's a list config item for "use these software platforms" and then anything in there which is the name of something in software_list_platforms is used for anything specific, and anything else it just launches the software with machine name = software name, or tries to and skips if something fails
#TODO: Don't blow up if MAME's not installed or anything like that
#TODO: More command line options from here for debugging, like only output launchers for one particular platform

class SoftwareListPlatform():
	def __init__(self, name, lists, launch_params_function):
		self.name = name
		self.lists = lists
		self.launch_params_function = launch_params_function

	def get_launch_params(self, software):
		return self.launch_params_function(software)

def _launch_with_software(system_name, software):
	#Use fully qualified id with : here to avoid ambiguity
	return mame_base(system_name, software=software.id)

def _quizwiz(software):
	return _launch_with_software('quizwizc', software)

def _neo_geo(software):
	#TODO: Plug in a memory card
	compat = software.software.compatibility
	if compat and 'AES' not in compat:
		raise EmulationNotSupportedException('Not compatible with AES')
	return _launch_with_software('aes', software)

def _super_cassette_vision(software):
	machine = 'scv_pal' if software.metadata.tv_type == TVSystem.PAL else 'scv'
	return _launch_with_software(machine, software)

software_list_platforms = [
	#For simplicity we're just going to only use certain lists at the moment, I'm very sorry
	#TODO: Will also need required_romset, and do -verifyroms on that to see that it's launchable; e.g. no point doing Neo Geo if -verifyroms aes fails, maybe like a main_driver so we get our CPU/screen/etc info from there, and we can skip it if broken and if main_config.exclude_non_working and machine.emulation_status == EmulationStatus.Broken and machine.basename not in main_config.non_working_whitelist: skip
	SoftwareListPlatform('Coleco Quiz Wiz', {MediaType.Cartridge: ['quizwiz']}, _quizwiz),
	SoftwareListPlatform('Neo Geo', {MediaType.Cartridge: ['neogeo']}, _neo_geo),
	SoftwareListPlatform('Super Cassette Vision', {MediaType.Cartridge: ['scv']}, _super_cassette_vision),
	#jakks stuff (set these up all as platform = Plug & Play)
	#vii (maybe this should be platform = Plug & Play? Or just "Vii")
	#nes
	#nes_ntbrom
	#ekara stuff
	#icanguit
	#icanpian

	#Not working:
	#rx78 (albeit kinda works)
	#tvgogo
	#c65
	#n64dd
]

class SoftwareLauncher():
	def __init__(self, software, platform, media_type):
		self.software = software
		self.platform = platform
		self.media_type = media_type

		self.metadata = Metadata()

	@property
	def id(self):
		return '{0}:{1}'.format(self.software.software_list.name, self.software.name)

	def make_launcher(self):
		if main_config.skip_mame_non_working_software:
			if self.metadata.specific_info.get('MAME-Emulation-Status', EmulationStatus.Unknown) == EmulationStatus.Broken:
				raise EmulationNotSupportedException('Not supported')

		launch_params = launchers.LaunchParams('mame', self.platform.get_launch_params(self))

		launchers.make_launcher(launch_params, self.software.description, self.metadata, 'MAME software', self.id)

def add_software_metadata(software):
	software.metadata.emulator_name = 'MAME' #Will probably always be the case
	#TODO: Metadata:
	#categories (but how?)
	#languages (detect from regions)
	#save_type
	#cpu_info, screen_info, input_info
	#regions (from filename tags)
	#nsfw? (if possible to detect from filename tags)
	#Is notes automatic from software?
	#disc_number, disc_total: From part stuff
	#tv_type: From region/tags
	
	software.metadata.platform = software.platform.name
	software.metadata.media_type = software.media_type
	
	software.software.add_standard_metadata(software.metadata)

def add_software(software):
	add_software_metadata(software)

	#TODO: main_config.use_mame_arcade_icons and such

	try:
		software.make_launcher()
	except EmulationNotSupportedException as ex:
		if main_config.debug:
			print('Could not launch {0} because {1}'.format(software.id, ex))

def add_software_list_platform(platform):
	for media_type, lists in platform.lists.items():
		for list_name in lists:
			software_list = get_software_list_by_name(list_name)
			if not software_list:
				continue
			available_software = software_list.get_available_software()
			for software_item in available_software:
				software = SoftwareLauncher(software_item, platform, media_type)
				add_software(software)

def add_mame_software():
	time_started = time.perf_counter()

	for platform in software_list_platforms:
		add_software_list_platform(platform)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('MAME software finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

if __name__ == '__main__':
	add_mame_software()
