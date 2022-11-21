import logging
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, cast
from xml.etree import ElementTree

try:
	from Crypto.Cipher import AES
	have_pycrypto = True
except ModuleNotFoundError:
	have_pycrypto = False

from meowlauncher.config.platform_config import platform_configs
from meowlauncher.games.roms.rom import FileROM, FolderROM
from meowlauncher.info import Date
from meowlauncher.platform_types import WiiTitleType
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric, load_dict)

from .common.gamecube_wii_common import (NintendoDiscRegion, _tdb,
                                         add_gamecube_wii_disc_metadata,
                                         just_read_the_wia_rvz_header_for_now)
from .common.gametdb import add_info_from_tdb
from .common.nintendo_common import AgeRatingStatus, NintendoAgeRatings, add_ratings_info

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.info import GameInfo

logger = logging.getLogger(__name__)

_nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')

_wii_config = platform_configs.get('Wii')

class WiiVirtualConsolePlatform(Enum):
	"""Indicates what platform a Virtual Console title originally emulates"""
	Commodore64 = 'C'
	Arcade = 'E' #Includes Neo Geo
	NES = 'F' #F for Famicom presumably
	SNES = 'J'
	MasterSystem = 'L'
	MegaDrive = 'M'
	N64 = 'N'
	PCEngine = 'P'
	PCEngineCD = 'Q'
	MSX = 'X' #Baaaaahhhh this is also used for WiiWare demos and how are we gonna differentiate that

def _round_up_to_multiple(num: int, factor: int) -> int:
	return num + (factor - (num % factor)) % factor

class WiiRatings(NintendoAgeRatings):
	"""Parses age rating bitfield inside disc """
	@staticmethod
	def _get_rating_status(byte: int) -> AgeRatingStatus:
		#Maybe? (See MadWorld (Europe) Germany rating)		
		if byte & 0b0100_0000:
			return AgeRatingStatus.Banned
		return NintendoAgeRatings._get_rating_status(byte)

def _parse_tmd(metadata: 'GameInfo', tmd: bytes) -> None:
	#Stuff that I dunno about: 0 - 388
	if tmd[387]:
		metadata.specific_info['Is vWii?'] = True
	#IOS version: 388-396
	#Title ID is just title type + hex product code, so don't worry about that

	try:
		metadata.specific_info['Title Type'] = WiiTitleType(int.from_bytes(tmd[396:400], 'big'))
	except ValueError:
		pass

	product_code = None
	try:
		product_code = tmd[400:404].decode('ascii')
		metadata.product_code = product_code

		if product_code:
			try:
				metadata.specific_info['Virtual Console Platform'] = WiiVirtualConsolePlatform(product_code[0])
			except ValueError:
				pass
	except UnicodeDecodeError:
		pass
	#Title flags: 404-408
	maker_code = None
	try:
		maker_code = convert_alphanumeric(tmd[408:410])
		if maker_code in _nintendo_licensee_codes:
			metadata.publisher = _nintendo_licensee_codes[maker_code]
	except NotAlphanumericException:
		pass
	
	if product_code:
		#Inconsistently enough WiiWare doesn't require appending the maker code, apparently
		add_info_from_tdb(_tdb, metadata, product_code)

	#Unused: 410-412
	region_code = int.from_bytes(tmd[412:414], 'big')
	try:
		metadata.specific_info['Region Code'] = NintendoDiscRegion(region_code)
	except ValueError:
		pass
	add_ratings_info(metadata, WiiRatings(tmd[414:430]))
	#Reserved: 430-442
	#IPC mask: 442-454 (wat?)
	#Reserved 2: 454-472
	#Access rights: 472-476
	metadata.specific_info['Revision'] = int.from_bytes(tmd[476:478], 'big')

def _parse_opening_bnr(metadata: 'GameInfo', opening_bnr: bytes) -> None:
	"""We will not try and bother parsing banner.bin or icon.bin, that would take a lot of effort"""
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
		7: 'Chinese', #Not sure if this is one of Simplified/Traditional Chinese and the unknown language is the other?
		8: 'Unknown Language',
		9: 'Korean',
	}
	names = {}
	for i, language in languages.items():
		try:
			name = imet[92 + (i * 84): 92 + (i * 84) + 84].rstrip(b'\0 ').decode('utf-16be')
			if name:
				names[language] = name
		except UnicodeDecodeError:
			continue #I guess
		#Why 84 characters long? Who knows
		#It seems \x00 is sometimes in the middle as some type of line/subtitle separator?
		#We will probably not really want to try and infer supported languages by what is not zeroed out here, I don't think that's how it works

	region_code = metadata.specific_info.get('Region Code')
	local_title = None
	if region_code == NintendoDiscRegion.NTSC_J:
		local_title = names.get('Japanese')
	elif region_code == NintendoDiscRegion.NTSC_K:
		local_title = names.get('Korean')
	elif region_code in (NintendoDiscRegion.NTSC_U, NintendoDiscRegion.PAL, NintendoDiscRegion.RegionFree):
		#This is still a bit anglocentric of me to ignore European languages, but eh
		local_title = names.get('English')
	elif names: #and region_code is None, which I would think shouldn't happen too often
		local_title = next(iter(names.values()))

	if local_title:
		metadata.add_alternate_name(local_title, 'Banner Title')
	for lang, title in names.items():
		if title != local_title:
			metadata.add_alternate_name(title, f'{lang} Banner Title')
	
def _add_wad_metadata(rom: FileROM, metadata: 'GameInfo') -> None:
	header = rom.read(amount=0x40)
	header_size = int.from_bytes(header[0:4], 'big')
	#WAD type: 4-8
	cert_chain_size = int.from_bytes(header[8:12], 'big')
	#Reserved: 12-16
	ticket_size = int.from_bytes(header[16:20], 'big')
	tmd_size = int.from_bytes(header[20:24], 'big')
	data_size = int.from_bytes(header[24:28], 'big')
	footer_size = int.from_bytes(header[28:32], 'big')

	#All blocks are stored in that order: header > cert chain > ticket > TMD > data; aligned to multiple of 64 bytes

	cert_chain_offset = _round_up_to_multiple(header_size, 64)
	ticket_offset = cert_chain_offset + _round_up_to_multiple(cert_chain_size, 64)
	tmd_offset = ticket_offset + _round_up_to_multiple(ticket_size, 64)

	real_tmd_size = _round_up_to_multiple(tmd_size, 64)
	if real_tmd_size >= 768:
		tmd = rom.read(seek_to=tmd_offset, amount=real_tmd_size)
		_parse_tmd(metadata, tmd)

	data_offset = tmd_offset + _round_up_to_multiple(tmd_size, 64)
	footer_offset = data_offset + _round_up_to_multiple(data_size, 64)
	#Dolphin suggests that this is opening.bnr actually
	footer = rom.read(seek_to=footer_offset, amount=_round_up_to_multiple(footer_size, 64))
	_parse_opening_bnr(metadata, footer)

def add_wii_homebrew_metadata(rom: FolderROM, game_info: 'GameInfo') -> None:
	game_info.specific_info['Executable Name'] = rom.relevant_files['boot.dol'].name

	icon_path = rom.get_file('icon.png', True)
	if icon_path:
		game_info.images['Banner'] = icon_path
		#Unfortunately the aspect ratio means it's not really great as an icon

	xml_path = rom.relevant_files['meta.xml']
	if xml_path.is_file():
		try:
			meta_xml = ElementTree.parse(xml_path)
			name = meta_xml.findtext('name')
			if name:
				game_info.add_alternate_name(name, 'Banner Title')
				rom.ignore_name = True

			coder = meta_xml.findtext('coder')
			if not coder:
				coder = meta_xml.findtext('author')
			game_info.developer = game_info.publisher = coder

			version = meta_xml.findtext('version')
			if version:
				version = version.removeprefix('rev').removeprefix('r').lstrip()
				
				if version[0] != 'v':
					version = 'v' + version
				game_info.specific_info['Version'] = version

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
					year = actual_date.year
					month = actual_date.month
					day = actual_date.day
					game_info.release_date = Date(year, month, day)

			short_description = meta_xml.findtext('short_description')
			if short_description:
				game_info.descriptions['Description'] = short_description
			long_description = meta_xml.findtext('long_description')
			if long_description:
				game_info.descriptions['Long Description'] = long_description

		except ElementTree.ParseError:
			logger.info('Ah bugger Wii homebrew XML in %s has problems', rom, exc_info=True)

def _add_wii_disc_metadata(rom: FileROM, game_info: 'GameInfo') -> None:
	wii_header = rom.read(0x40_000, 0xf000)

	game_partition_offset = None
	for i in range(4):
		partition_group = wii_header[8 * i: (8 * i) + 8]
		partition_count = int.from_bytes(partition_group[0:4], 'big')
		partition_table_entry_offset = int.from_bytes(partition_group[4:8], 'big') << 2
		for j in range(partition_count):
			seek_to = partition_table_entry_offset + (j * 8)
			partition_table_entry = rom.read(seek_to, 8)
			partition_offset = int.from_bytes(partition_table_entry[0:4], 'big') << 2
			partition_type = int.from_bytes(partition_table_entry[4:8], 'big')
			#if partition_type > 0xf:
			#	#SSBB Masterpiece partitions use ASCII title IDs here; realistically other partition types should be 0 (game) 1 (update) or 2 (channel)
			#	partition_type = partition_table_entry[4:8].decode('ascii', errors='backslashreplace')

			#Seemingly most games have an update partition at 0x50_000 and a game partition at 0xf_800_000. That's just an observation though and may not be 100% the case
			if partition_type == 1:
				game_info.specific_info['Has Update Partition?'] = True
			elif partition_type == 0 and game_partition_offset is None:
				game_partition_offset = partition_offset

	common_key = None
	if _wii_config:
		common_key = _wii_config.options.get('common_key')
	if common_key:
		if game_partition_offset and have_pycrypto:
			game_partition_header = rom.read(game_partition_offset, 0x2c0)
			title_iv = game_partition_header[0x1dc:0x1e4] + (b'\x00' * 8)
			data_offset = int.from_bytes(game_partition_header[0x2b8:0x2bc], 'big') << 2

			master_key = bytes.fromhex(common_key)
			aes = AES.new(master_key, AES.MODE_CBC, title_iv)
			encrypted_key = game_partition_header[0x1bf:0x1cf]
			key = aes.decrypt(encrypted_key)

			chunk_offset = game_partition_offset + data_offset # + (index * 0x8000) but we only need 1st chunk (0x7c00 bytes of encrypted data each chunk)
			chunk = rom.read(chunk_offset, 0x8000)
			chunk_iv = chunk[0x3d0:0x3e0]
			aes = AES.new(key, AES.MODE_CBC, chunk_iv)
			decrypted_chunk = aes.decrypt(chunk[0x400:])

			#TODO: Try and read filesystem to see if there is an opening.bnr in there (should be)

			try:
				apploader_date = decrypted_chunk[0x2440:0x2450].rstrip(b'\0').decode('ascii')
				try:
					d = datetime.strptime(apploader_date, '%Y/%m/%d')
					game_info.specific_info['Build Date'] = Date(d.year, d.month, d.day)
					guessed = Date(d.year, d.month, d.day, True)
					if guessed.is_better_than(game_info.release_date):
						game_info.release_date = guessed
				except ValueError:
					pass
			except UnicodeDecodeError:
				pass

	#Unused (presumably would be region-related stuff): 0xe004:0xe010
	region_code = int.from_bytes(wii_header[0xe000:0xe004], 'big')
	try:
		game_info.specific_info['Region Code'] = NintendoDiscRegion(region_code)
	except ValueError:
		pass
	add_ratings_info(game_info, WiiRatings(wii_header[0xe010:0xe020]))

def add_wii_custom_info(game: 'ROMGame') -> None:
	if game.rom.extension in {'gcz', 'iso', 'wbfs', 'gcm'}:
		header: bytes
		rom = cast(FileROM, game.rom)
		if game.rom.extension in {'iso', 'gcm', 'gcz'}:
			#.gcz can be a format for Wii discs, though not recommended and uncommon
			header = rom.read(0, 0x2450)
		elif game.rom.extension == 'wbfs':
			header = rom.read(amount=0x2450, seek_to=0x200)
		add_gamecube_wii_disc_metadata(rom, game.info, header)
		_add_wii_disc_metadata(rom, game.info)
	elif game.rom.extension == 'wad':
		_add_wad_metadata(cast(FileROM, game.rom), game.info)
	elif game.rom.is_folder:
		add_wii_homebrew_metadata(cast(FolderROM, game.rom), game.info)
	elif game.rom.extension in {'dol', 'elf'}:
		if game.rom.name.lower() == 'boot': #Shouldn't happen I guess if homebrew detection works correctly but sometimes it be like that
			game.info.categories = game.info.categories[:-1]
			game.info.add_alternate_name(game.rom.path.parent.name, 'Folder Name')
			game.rom.ignore_name = True
	elif game.rom.extension in {'wia', 'rvz'}:
		just_read_the_wia_rvz_header_for_now(cast(FileROM, game.rom), game.info)
