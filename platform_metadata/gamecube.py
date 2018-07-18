
from metadata import CPUInfo, ScreenInfo, Screen
from common import convert_alphanumeric, NotAlphanumericException
from platform_metadata.nintendo_common import nintendo_licensee_codes


def add_gamecube_wii_disc_metadata(game):
	header = game.rom.read(amount=32)
	#Actually, the header is quite a bit bigger than that. We don't really need the disc name or filesystem offset or anything like that, though.
	try:
		game.metadata.specific_info['Product-Code'] = convert_alphanumeric(header[:4])
	except NotAlphanumericException:
		pass

	try:
		licensee_code = convert_alphanumeric(header[4:6])
		if licensee_code in nintendo_licensee_codes:
			game.metadata.author = nintendo_licensee_codes[licensee_code]
	except NotAlphanumericException:
		pass

def add_gamecube_system_info(game):
	cpu_info = CPUInfo()
	cpu_info.main_cpu = 'IBM PowerPC 603'
	cpu_info.clock_speed = 485 * 1000 * 1000
	game.metadata.cpu_info = cpu_info

	screen = Screen()
	screen.width = 640
	screen.height = 480
	screen.type = 'raster'
	screen.tag = 'screen'
	screen.refresh_rate = 60  

	screen_info = ScreenInfo()
	screen_info.screens = [screen]
	game.metadata.screen_info = screen_info
	
def add_gamecube_metadata(game):
	add_gamecube_system_info(game)

	if game.rom.extension == 'gcz' or game.rom.extension == 'tgc':
		#Nuh uh. Not touching weird formats. Not today.
		return
	
	if game.rom.extension == 'iso':
		add_gamecube_wii_disc_metadata(game)
