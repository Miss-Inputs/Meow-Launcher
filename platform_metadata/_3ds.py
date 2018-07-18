
from info.region_info import TVSystem
from metadata import CPUInfo, ScreenInfo, Screen
from common import convert_alphanumeric, NotAlphanumericException
from platform_metadata.nintendo_common import nintendo_licensee_codes

#TODO: Can get the following info:
#Presence of executable content (need that), electronic manual, Download Play child, and update data
#Author (from licensee list). Can also get publisher name from SMDH
#Product code (should skip if CTR-P-CTAP)
#Executable content partition is executable (one of these things differentiates things like update data in .cxi format, so I can say hey don't make a launcher for the SSB4 1.1.6 patch that's silly)
#Region locking info (inside ExeFS filesystem which may be a bit involved, or in .smdh file next to homebrew)

#Save type is either SaveType.MemoryCard (for SD card saves) or SaveType.Internal. So... hmm... there's some flags in SMDH about warning about save data when closing... hmm... are there even games/software that wouldn't save at all?


def add_3ds_system_info(game):
	cpu_info = CPUInfo()
	cpu_info.main_cpu = 'ARM11'
	cpu_info.clock_speed = 268 * 1000 * 1000 #New 3DS is 804 MHz	
	game.metadata.cpu_info = cpu_info

	top_screen = Screen()
	top_screen.width = 400
	top_screen.height = 200
	top_screen.type = 'lcd'
	top_screen.tag = 'top'
	top_screen.refresh_rate = 59.834
	
	bottom_screen = Screen()
	bottom_screen.width = 320
	bottom_screen.height = 200
	bottom_screen.type = 'lcd'
	bottom_screen.tag = 'bottom'
	bottom_screen.refresh_rate = 59.834
	
	screen_info = ScreenInfo()
	screen_info.screens = [top_screen, bottom_screen]
	game.metadata.screen_info = screen_info

def add_3ds_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	add_3ds_system_info(game)
