import os
import statistics
import xml.etree.ElementTree as ElementTree
from datetime import datetime

from common import NotAlphanumericException, convert_alphanumeric
from config import main_config
from data.nintendo_licensee_codes import nintendo_licensee_codes
from metadata import CPU, Screen, ScreenInfo

from .gamecube_wii_common import (NintendoDiscRegion,
                                  add_gamecube_wii_disc_metadata)

try:
	from Crypto.Cipher import AES
	have_pycrypto = True
except ModuleNotFoundError:
	have_pycrypto = False

def add_wii_system_info(game):
	cpu = CPU()
	cpu.chip_name = 'IBM PowerPC 750CL'
	cpu.clock_speed = 729 * 1000 * 1000
	game.metadata.cpu_info.add_cpu(cpu)

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
	return num + (factor - (num % factor)) % factor

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
	region_code = int.from_bytes(tmd[412:414], 'big')
	try:
		game.metadata.specific_info['Region-Code'] = NintendoDiscRegion(region_code)
	except ValueError:
		pass
	parse_ratings(game, tmd[414:430])
	#Reserved: 430-442
	#IPC mask: 442-454 (wat?)
	#Reserved 2: 454-472
	#Access rights: 472-476
	game.metadata.specific_info['Revision'] = int.from_bytes(tmd[476:478], 'big')

def parse_opening_bnr(game, opening_bnr):
	#We will not try and bother parsing banner.bin or icon.bin, that would take a lot of effort
	imet = opening_bnr[64:]
	#I don't know why this is 64 bytes in, aaaa

	#Padding: 0-64
	magic = imet[64:68]
	if magic != b'IMET':
		return
	#Hash size: 68-72
	#Unknown: 72-76
	#icon.bin size: 76-80
	#banner.bin size: 80-84
	#sound.bin size: 84-88
	#Unknown flag: 88-92
	languages = {
		0: 'Japanese',
		1: 'English',
		2: 'German',
		3: 'French',
		4: 'Spanish',
		5: 'Italian',
		6: 'Dutch',
		7: 'Unknown Language 1', #These may be simplified and traditional Chinese respectively?
		8: 'Unknown Language 2',
		9: 'Korean',
	}
	names = {}
	for i in range(10):
		try:
			name = imet[92 + (i * 84): 92 + (i * 84) + 84].decode('utf-16be').rstrip('\0')
			if name:
				names[languages[i]] = name
		except UnicodeDecodeError:
			continue #I guess
		#Why 84 characters long? Who knows
		#It seems \x00 is sometimes in the middle as some type of line/subtitle separator?
		#We will probably not really want to try and infer supported languages by what is not zeroed out here, I don't think that's how it works

	for lang, title in names.items():
		game.metadata.specific_info['{0}-Banner-Title'.format(lang.replace(' ', '-'))] = title
	
	region_code = game.metadata.specific_info.get('Region-Code')
	local_title = None
	if region_code == NintendoDiscRegion.NTSC_J:
		local_title = names.get('Japanese')
	elif region_code == NintendoDiscRegion.NTSC_K:
		local_title = names.get('Korean')
	elif region_code in (NintendoDiscRegion.NTSC_U, NintendoDiscRegion.PAL, NintendoDiscRegion.RegionFree):
		#This is still a bit anglocentric of me to ignore European languages, but eh
		local_title = names.get('English')
	elif names: #and region_code is None, which I would think shouldn't happen too often
		local_title = list(names.values())[0]

	if local_title:
		game.metadata.specific_info['Banner-Title'] = local_title

def add_wad_metadata(game):
	header = game.rom.read(amount=0x40)
	header_size = int.from_bytes(header[0:4], 'big')
	#WAD type: 4-8
	cert_chain_size = int.from_bytes(header[8:12], 'big')
	#Reserved: 12-16
	ticket_size = int.from_bytes(header[16:20], 'big')
	tmd_size = int.from_bytes(header[20:24], 'big')
	data_size = int.from_bytes(header[24:28], 'big')
	footer_size = int.from_bytes(header[28:32], 'big')

	#All blocks are stored in that order: header > cert chain > ticket > TMD > data; aligned to multiple of 64 bytes

	cert_chain_offset = round_up_to_multiple(header_size, 64)
	ticket_offset = cert_chain_offset + round_up_to_multiple(cert_chain_size, 64)
	tmd_offset = ticket_offset + round_up_to_multiple(ticket_size, 64)

	tmd = game.rom.read(seek_to=tmd_offset, amount=round_up_to_multiple(tmd_size, 64))
	parse_tmd(game, tmd)

	data_offset = tmd_offset + round_up_to_multiple(tmd_size, 64)
	footer_offset = data_offset + round_up_to_multiple(data_size, 64)
	#Dolphin suggests that this is opening.bnr actually
	footer = game.rom.read(seek_to=footer_offset, amount=round_up_to_multiple(footer_size, 64))
	parse_opening_bnr(game, footer)

def add_wii_homebrew_metadata(game):
	icon_path = os.path.join(game.folder, 'icon.png')
	if os.path.isfile(icon_path):
		game.metadata.images['Banner'] = icon_path
		#Unfortunately the aspect ratio means it's not really great as an icon

	xml_path = os.path.join(game.folder, 'meta.xml')
	if os.path.isfile(xml_path):
		#boot is not a helpful launcher name
		game.metadata.categories = game.metadata.categories[:-1]
		try:
			meta_xml = ElementTree.parse(xml_path)
			name = meta_xml.findtext('name')
			if name:
				game.metadata.specific_info['Title'] = name
				game.rom.name = name

			coder = meta_xml.findtext('coder')
			if not coder:
				coder = meta_xml.findtext('author')
			game.metadata.developer = game.metadata.publisher = coder

			version = meta_xml.findtext('version')
			if version:
				if version.startswith('rev'):
					version = version[3:].lstrip()
				elif version.startswith('r'):
					version = version[1:].lstrip()
				
				if version[0] != 'v':
					version = 'v' + version
				game.metadata.specific_info['Version'] = version

			release_date = meta_xml.findtext('release_date')
			if release_date:
				#Not interested in hour/minute/second/etc
				release_date = release_date[0:8]
				actual_date = None
				date_formats = [
					'%Y%m%d', #The one actually specified by the meta.xml format
					'%Y%m%d%H%M%S',
					'%d/%m/%Y', #Hmm this might be risky because of potential ambiguity with American dates
					'%Y-%m-%d',
				]
				for date_format in date_formats:
					try:
						actual_date = datetime.strptime(release_date, date_format)
						break
					except ValueError:
						continue
				if actual_date:
					game.metadata.year = actual_date.year
					game.metadata.month = actual_date.strftime('%B')
					game.metadata.day = actual_date.day

			short_description = meta_xml.findtext('short_description')
			if short_description:
				game.metadata.specific_info['Description'] = short_description
			long_description = meta_xml.findtext('long_description')
			if short_description:
				game.metadata.specific_info['Long-Description'] = long_description

		except ElementTree.ParseError as etree_error:
			if main_config.debug:
				print('Ah bugger this Wii homebrew XML has problems', game.rom.path, etree_error)
			game.rom.name = os.path.basename(game.folder)

def parse_ratings(game, ratings_bytes, invert_has_rating_bit=False, use_bit_6=True):
	ratings = {}
	for i, rating in enumerate(ratings_bytes):
		#We could go into which ratings board each position in the ratings bytes means, or what the ratings are called for each age, but there's no need to do that for this purpose
		has_rating = (rating & 0b1000_0000) == 0 #For 3DS and DSi, the meaning of this bit is inverted
		if invert_has_rating_bit:
			has_rating = not has_rating
		if use_bit_6:
			banned = rating & 0b0100_0000 #Seems to only mean this for Wii (MadWorld (Europe) has this bit set for Germany rating); on Wii U it seems to be "this rating is unused" and 3DS and DSi I dunno but it probably doesn't work that way
		else:
			banned = False
		#Bit 5 I'm not even sure about (on Wii it seems to be "includes online interactivity"), but we can ignore it
		#The last 4 bits are the actual rating
		if has_rating and not banned:
			ratings[i] = rating & 0b0001_1111
	
	ratings_list = list(ratings.values())
	if not ratings_list:
		return

	#If there is only one rating or they are all the same, this covers that; otherwise if ratings boards disagree this is probably the best way to interpret that situation
	try:
		rating = statistics.mode(ratings_list)
	except statistics.StatisticsError:
		rating = max(ratings_list)

	game.metadata.specific_info['Age-Rating'] = rating
	game.metadata.nsfw = rating >= 18

def add_wii_disc_metadata(game):
	wii_header = game.rom.read(0x40_000, 0xf000)

	game_partition_offset = None
	for i in range(4):
		partition_group = wii_header[8 * i: (8 * i) + 8]
		partition_count = int.from_bytes(partition_group[0:4], 'big')
		partition_table_entry_offset = int.from_bytes(partition_group[4:8], 'big') << 2
		for j in range(partition_count):
			seek_to = partition_table_entry_offset + (j * 8)
			partition_table_entry = game.rom.read(seek_to, 8)
			partition_offset = int.from_bytes(partition_table_entry[0:4], 'big') << 2
			partition_type = int.from_bytes(partition_table_entry[4:8], 'big')
			if partition_type > 0xf:
				#SSBB Masterpiece partitions use ASCII title IDs here; realistically other partition types should be 0 (game) 1 (update) or 2 (channel)
				partition_type = partition_table_entry[4:8].decode('ascii', errors='backslashreplace')

			#Seemingly most games have an update partition at 0x50_000 and a game partition at 0xf_800_000. That's just an observation though and may not be 100% the case
			#print(game.rom.path, 'has partition type', partition_type, 'at', hex(partition_offset))
			if partition_type == 1:
				game.metadata.specific_info['Has-Update-Partition'] = True
			elif partition_type == 0 and game_partition_offset is None:
				game_partition_offset = partition_offset

	wii_common_key = main_config.wii_common_key
	if wii_common_key:
		if game_partition_offset and have_pycrypto:
			game_partition_header = game.rom.read(game_partition_offset, 0x2c0)
			title_iv = game_partition_header[0x1dc:0x1e4] + (b'\x00' * 8)
			data_offset = int.from_bytes(game_partition_header[0x2b8:0x2bc], 'big') << 2

			master_key = bytes.fromhex(wii_common_key)
			aes = AES.new(master_key, AES.MODE_CBC, title_iv)
			encrypted_key = game_partition_header[0x1bf:0x1cf]
			key = aes.decrypt(encrypted_key)

			chunk_offset = game_partition_offset + data_offset # + (index * 0x8000) but we only need 1st chunk (0x7c00 bytes of encrypted data each chunk)
			chunk = game.rom.read(chunk_offset, 0x8000)
			chunk_iv = chunk[0x3d0:0x3e0]
			aes = AES.new(key, AES.MODE_CBC, chunk_iv)
			decrypted_chunk = aes.decrypt(chunk[0x400:])

			#TODO: Try and read filesystem to see if there is an opening.bnr in there (should be)

			try:
				apploader_date = decrypted_chunk[0x2440:0x2450].decode('ascii').rstrip('\0')
				#Not quite release date but it will do
				try:
					actual_date = datetime.strptime(apploader_date, '%Y/%m/%d')
					game.metadata.year = actual_date.year
					game.metadata.month = actual_date.strftime('%B')
					game.metadata.day = actual_date.day
				except ValueError:
					pass
			except UnicodeDecodeError:
				pass

	#Unused (presumably would be region-related stuff): 0xe004:0xe010
	region_code = int.from_bytes(wii_header[0xe000:0xe004], 'big')
	try:
		game.metadata.specific_info['Region-Code'] = NintendoDiscRegion(region_code)
	except ValueError:
		pass
	parse_ratings(game, wii_header[0xe010:0xe020])

def add_wii_metadata(game):
	add_wii_system_info(game)
	if game.rom.extension in ('gcz', 'iso', 'wbfs', 'gcm'):
		if game.rom.extension in ('iso', 'gcm', 'gcz'):
			#.gcz can be a format for Wii discs, though not recommended and uncommon
			header = game.rom.read(0, 0x2450)
		elif game.rom.extension == 'wbfs':
			header = game.rom.read(amount=0x2450, seek_to=0x200)
		add_gamecube_wii_disc_metadata(game, header)
		add_wii_disc_metadata(game)
	elif game.rom.extension == 'wad':
		add_wad_metadata(game)
	elif game.rom.extension in ('dol', 'elf'):
		add_wii_homebrew_metadata(game)
