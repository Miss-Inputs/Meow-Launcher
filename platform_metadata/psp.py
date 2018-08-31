import os

from info.region_info import TVSystem
from metadata import CPUInfo, ScreenInfo, Screen

#You can get product code, disc number, number of discs, and a whole lot of other stuff... for PBP files. Maybe there's an ISO9660 library we can use, just for this kind of thing...

def add_psp_system_info(game):
	cpu_info = CPUInfo()
	cpu_info.main_cpu = 'Sony CXD2962GG'
	cpu_info.clock_speed = 333 * 1000 * 1000
	game.metadata.cpu_info = cpu_info

	screen = Screen()
	screen.width = 480
	screen.height = 272
	screen.type = 'lcd'
	screen.tag = 'screen'
	screen.refresh_rate = 60  #I presume so, anyway... good luck finding actual information. I bet it's not really exactly 60Hz

	screen_info = ScreenInfo()
	screen_info.screens = [screen]
	game.metadata.screen_info = screen_info

def add_psp_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	add_psp_system_info(game)

	if game.rom.extension == 'pbp':
		#These are basically always named EBOOT.PBP (due to how PSPs work I guess), so that's not a very good launcher name, and use the folder it's stored in instead
		game.rom.name = os.path.basename(game.folder)
