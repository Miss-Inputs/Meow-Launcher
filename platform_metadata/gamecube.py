from datetime import datetime

import cd_read
from metadata import CPUInfo, ScreenInfo, Screen
from common import convert_alphanumeric, NotAlphanumericException
from .nintendo_common import nintendo_licensee_codes

#TODO: Maybe get disc number and region code?

def add_gamecube_wii_disc_metadata(game, header):
	internal_title = header[32:64] #Potentially quite a lot bigger but we don't need that much out of it
	if internal_title[:28] == b'GAMECUBE HOMEBREW BOOTLOADER':
		return

	product_code = None
	try:
		product_code = convert_alphanumeric(header[:4])
	except NotAlphanumericException:
		pass

	publisher = None
	try:
		licensee_code = convert_alphanumeric(header[4:6])
		if licensee_code in nintendo_licensee_codes:
			publisher = nintendo_licensee_codes[licensee_code]
		elif licensee_code != '00':
			publisher = '<unknown Nintendo licensee {0}>'.format(licensee_code)
	except NotAlphanumericException:
		pass

	ignore_game_id = False
	if product_code == 'RELS' and licensee_code == 'AB':
		#This is found on a few prototype discs, it's not valid
		ignore_game_id = True

	if not ignore_game_id:
		game.metadata.product_code = product_code
		game.metadata.publisher = publisher

	game.metadata.revision = header[7]
	is_wii = header[0x18:0x1c] == b']\x1c\x9e\xa3'
	is_gamecube = header[0x1c:0x20] == b'\xc23\x9f='
	#Is this ever set to both? In theory no, but... hmm

	if is_gamecube:
		game.metadata.platform = 'GameCube'
		try:
			apploader_date = header[0x2440:0x2450].decode('ascii').rstrip('\x00')
			try:
				actual_date = datetime.strptime(apploader_date, '%Y/%m/%d')
				game.metadata.year = actual_date.year
				game.metadata.month = actual_date.strftime('%B')
				game.metadata.day = actual_date.day
			except ValueError:
				pass
		except UnicodeDecodeError:
			pass
	elif is_wii:
		game.metadata.platform = 'Wii'
	else:
		game.metadata.specific_info['No-Disc-Magic'] = True

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

	#TODO: TGC, dol

	if game.rom.extension in ('gcz', 'iso', 'gcm'):
		if game.rom.extension == 'gcz':
			header = cd_read.read_gcz(game.rom.path, amount=0x2450)
		elif game.rom.extension in ('iso', 'gcm'):
			header = game.rom.read(amount=0x2450)
		add_gamecube_wii_disc_metadata(game, header)
