import os
import xml.etree.ElementTree as ElementTree
from datetime import datetime

import cd_read
from common import convert_alphanumeric, NotAlphanumericException
from config import main_config
from metadata import CPUInfo, ScreenInfo, Screen
from platform_metadata.gamecube import add_gamecube_wii_disc_metadata
from .nintendo_common import nintendo_licensee_codes

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

def round_up_to_multiple(num, factor):
	multiple = num % factor
	remainder = num - multiple
	#I feel like those variable names are swapped around, but eh, as long as it does the thing
	if multiple > (factor / 2):
		remainder += factor
	return remainder

def parse_tmd(game, tmd):
	#Stuff that I dunno about: 0 - 388
	#IOS version: 388-396
	#Title ID: 396-400
	try:
		product_code = tmd[400:404].decode('ascii')
		game.metadata.product_code = product_code
	except UnicodeDecodeError:
		pass
	#Product code format is like that of GameCube/Wii discs, we could get country or type from it I guess
	#Title flags: 404-408
	try:
		maker_code = convert_alphanumeric(tmd[408:410])
		if maker_code in nintendo_licensee_codes:
			game.metadata.publisher = nintendo_licensee_codes[maker_code]
	except NotAlphanumericException:
		pass
	#Unused: 410-412
	#Region code: 412-414, should I do that? (Can't really infer game.metadata.regions though, I guess we can infer TV-Type but that's not really relevant on Wii, you'd want region locking stuff if anything)
	#Ratings: 414-430 (could use this for game.metadata.nsfw I guess)
	#Reserved: 430-442
	#IPC mask: 442-454 (wat?)
	#Reserved 2: 454-472
	#Access rights: 472-476
	game.metadata.revision = int.from_bytes(tmd[476:478], 'big')

def add_wad_metadata(game):
	header = game.rom.read(amount=0x40)
	#Header size: 0-4 (do I need that?)
	#WAD type: 4-8
	cert_chain_size = int.from_bytes(header[8:12], 'big')
	#Reserved: 12-16
	ticket_size = int.from_bytes(header[16:20], 'big')
	tmd_size = int.from_bytes(header[20:24], 'big')
	#Data size: 24-28
	#Footer size: 28-32

	#All blocks are stored in that order: header > cert chain > ticket > TMD > data; aligned to multiple of 64 bytes
	#Should this be (round_up_to_multiple(header size)) + round_up_to_multiple(cert size) + round_up_to_multiple(ticket size)?
	tmd_offset = 64 + round_up_to_multiple(cert_chain_size, 64) + round_up_to_multiple(ticket_size, 64)

	tmd = game.rom.read(seek_to=tmd_offset, amount=round_up_to_multiple(tmd_size, 64))
	parse_tmd(game, tmd)

def add_wii_homebrew_metadata(game):
	icon_path = os.path.join(game.folder, 'icon.png')
	if os.path.isfile(icon_path):
		game.metadata.images['Banner'] = icon_path
		#Unfortunately the aspect ratio means it's not really great as an icon

	xml_path = os.path.join(game.folder, 'meta.xml')
	if os.path.isfile(xml_path):
		#boot is not a helpful launcher name
		try:
			meta_xml = ElementTree.parse(xml_path)
			game.rom.name = meta_xml.findtext('name')

			coder = meta_xml.findtext('coder')
			if not coder:
				coder = meta_xml.findtext('author')
			game.metadata.developer = coder

			release_date = meta_xml.findtext('release_date')
			if release_date:
				#Not interested in hour/minute/second/etc
				release_date = release_date[0:8]
				try:
					actual_date = datetime.strptime(release_date, '%Y%m%d')
					game.metadata.year = actual_date.year
					game.metadata.month = actual_date.strftime('%B')
					game.metadata.day = actual_date.day
				except ValueError:
					pass
		except ElementTree.ParseError as etree_error:
			if main_config.debug:
				print('Ah bugger this Wii homebrew XML has problems', game.rom.path, etree_error)
			game.rom.name = os.path.basename(game.folder)


def add_wii_metadata(game):
	add_wii_system_info(game)
	if game.rom.extension in ('gcz', 'iso', 'wbfs'):
		if game.rom.extension == 'gcz':
			#Can be a format for Wii discs, though not recommended and uncommon
			header = cd_read.read_gcz(game.rom.path, amount=0x2450)
		elif game.rom.extension == 'iso':
			header = game.rom.read(amount=0x2450)
		elif game.rom.extension == 'wbfs':
			header = game.rom.read(amount=0x2450, seek_to=0x200)

		add_gamecube_wii_disc_metadata(game, header)
	elif game.rom.extension == 'wad':
		add_wad_metadata(game)
	elif game.rom.extension in ('dol', 'elf'):
		add_wii_homebrew_metadata(game)
