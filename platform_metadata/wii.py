import os
import xml.etree.ElementTree as ElementTree
import sys

from metadata import CPUInfo, ScreenInfo, Screen
from platform_metadata.gamecube import add_gamecube_wii_disc_metadata

#TODO: Get year for homebrew... although, the date format isn't consistent, so good luck with that.
#Could get region code info too, I guess

debug = '--debug' in sys.argv

def add_wii_system_info(game):
	cpu_info = CPUInfo()
	cpu_info.main_cpu = 'IBM PowerPC 603'
	cpu_info.clock_speed = 729 * 1000 * 1000
	game.metadata.cpu_info = cpu_info

	screen = Screen()
	screen.width = 640 
	screen.height = 480
	#Let's just go with that. PAL consoles can do 576i and interlacing confuses me (720x576?)
	#Also anamorphic widescreen doesn't count
	screen.type = 'raster'
	screen.tag = 'screen'
	screen.refresh_rate = 60  

	screen_info = ScreenInfo()
	screen_info.screens = [screen]
	game.metadata.screen_info = screen_info

def add_wii_metadata(game):
	add_wii_system_info(game)
	if game.rom.extension == 'iso':
		add_gamecube_wii_disc_metadata(game)

	#TODO WiiWare wad
	
	#TODO: Only do this if ext = dol or elf, not that you'd expect to see meta.xml anywhere else but who knows
	xml_path = os.path.join(game.folder, 'meta.xml')
	if os.path.isfile(xml_path):
		#boot is not a helpful launcher name
		try:
			meta_xml = ElementTree.parse(xml_path)
			game.rom.name = meta_xml.findtext('name')
			coder = meta_xml.findtext('coder')
			if not coder:
				coder = meta_xml.findtext('author')
			game.metadata.author = coder
		except ElementTree.ParseError as etree_error:
			if debug:
				print('Ah bugger', game.rom.path, etree_error)
			game.rom.name = os.path.basename(game.folder)
