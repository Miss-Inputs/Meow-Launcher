try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

import os
from collections.abc import Mapping
from enum import Enum
from typing import Optional, cast
from xml.etree import ElementTree

from meowlauncher import input_metadata
from meowlauncher.common_types import SaveType
from meowlauncher.config.main_config import main_config
from meowlauncher.config.platform_config import platform_configs
from meowlauncher.data.name_cleanup._3ds_publisher_overrides import \
    consistentified_manufacturers
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.games.roms.rom_game import ROMGame
from meowlauncher.metadata import Metadata
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric, junk_suffixes,
                                     load_dict)

from .common.gametdb import TDB, add_info_from_tdb
from .common.nintendo_common import (WiiU3DSRegionCode,
                                     add_info_from_local_titles, parse_ratings)

nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')


class _3DSVirtualConsolePlatform(Enum):
	GameBoy = 'R'
	GameBoyColor = 'Q'
	GameGear = 'G'
	NES = 'T'
	SNES = 'U'
	GBA = 'P'

languages = {
	0: 'Japanese',
	1: 'English',
	2: 'French',
	3: 'German',
	4: 'Italian',
	5: 'Spanish',
	6: 'Simplified Chinese',
	7: 'Korean',
	8: 'Dutch',
	9: 'Portugese',
	10: 'Russian',
	11: 'Traditional Chinese',
	12: 'Japanese', #Wait how's that work
	#Theoretically there could be 3 more languages here, but there are probably not
	13: 'Unknown language 1',
	14: 'Unknown language 2',
	15: 'Unknown language 3',
}
media_unit = 0x200

def add_3ds_system_info(metadata: Metadata):
	#Although we can't know for sure if the game uses the touchscreen, it's safe to assume that it probably does
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.analog_sticks = 1
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	builtin_gamepad.shoulder_buttons = 2

	controller = input_metadata.CombinedController([builtin_gamepad, input_metadata.Touchscreen()])
	metadata.input_info.add_option(controller)

def _load_tdb() -> Optional[TDB]:
	if not '3DS' in platform_configs:
		return None
	tdb_path = platform_configs['3DS'].options.get('tdb_path')
	if not tdb_path:
		return None

	try:
		tdb_parser = ElementTree.XMLParser()
		with open(tdb_path, 'rb') as tdb_file:
			#We have to do this the hard way because there is an invalid element in there
			for line in tdb_file:
				if line.lstrip().startswith(b'<3DSTDB'):
					continue
				tdb_parser.feed(line)
		return TDB(tdb_parser.close())
	except (ElementTree.ParseError, OSError) as blorp:
		if main_config.debug:
			print('Oh no failed to load 3DS TDB because', blorp)
		return None
tdb = _load_tdb()

def add_cover(metadata: Metadata, product_code: str):
	#Intended for the covers database from GameTDB
	covers_path = platform_configs['3DS'].options.get('covers_path')
	if not covers_path:
		return
	cover_path = covers_path.joinpath(product_code)
	for ext in ('png', 'jpg'):
		potential_cover_path = cover_path.with_suffix(os.extsep + ext)
		if potential_cover_path.is_file():
			metadata.images['Cover'] = potential_cover_path
			break

def parse_ncch(rom: FileROM, metadata: Metadata, offset: int):
	#Skip over SHA-256 siggy and magic
	header = rom.read(seek_to=offset + 0x104, amount=0x100)
	#Content size: 0-4 (media unit)
	#Partition ID: 4-12
	try:
		maker = convert_alphanumeric(header[12:14])
		if maker in nintendo_licensee_codes:
			metadata.publisher = nintendo_licensee_codes[maker]
	except NotAlphanumericException:
		pass
	#NCCH version: 14-16 (always 2?)
	metadata.specific_info['NCCH Version'] = int.from_bytes(header[14:16], 'little')
	#Something about a hash: 16-20
	#Program ID: 20-28
	#Reserved: 28-44
	#Logo region hash: 44-76
	try:
		product_code = header[76:86].decode('ascii')
		metadata.product_code = product_code
		#As usual, can get country and type from here, but it has more letters and as such you can also get category as well, or like... type 2 electric boogaloo. This also means we can't use convert_alphanumeric because it contains dashes, so I guess I need to fiddle with that method if I want to use it like that
		#(To be precise: P = retail/cart, N = digital only, M = DLC, T = demos, U = patches)
		try:
			metadata.specific_info['Virtual Console Platform'] = _3DSVirtualConsolePlatform(product_code[6])
		except ValueError:
			pass
		if len(product_code) == 10 and '\0' not in product_code:
			short_product_code = product_code[6:]
			add_info_from_tdb(tdb, metadata, short_product_code)
			add_cover(metadata, short_product_code)
	except UnicodeDecodeError:
		pass
	#Extended header hash: 92-124
	#Extended header size: 124-128
	#Reserved: 128-132
	flags = header[132:140]
	is_data = (flags[5] & 1) > 0
	is_executable = (flags[5] & 2) > 0
	is_not_cxi = is_data and not is_executable
	metadata.specific_info['Is CXI?'] = not is_not_cxi
	#Is system update = flags[5] & 4
	#Is electronic manual = flags[5] & 8
	#Is trial = flags[5] & 16
	#Is zero key encrypted = flags[7] & 1
	is_decrypted = (flags[7] & 4) > 0
	metadata.specific_info['Decrypted'] = is_decrypted

	plain_region_offset = (int.from_bytes(header[140:144], 'little') * media_unit) + offset
	plain_region_length = (int.from_bytes(header[144:148], 'little') * media_unit)
	#logo_region_offset = (int.from_bytes(header[148:152], 'little') * media_unit) + offset
	#logo_region_length = (int.from_bytes(header[152:156], 'little') * media_unit)
	exefs_offset = (int.from_bytes(header[156:160], 'little') * media_unit) + offset
	exefs_length = (int.from_bytes(header[160:164], 'little') * media_unit)
	#romfs_offset = (int.from_bytes(header[172:176], 'little') * media_unit) + offset
	#romfs_length = (int.from_bytes(header[176:180], 'little') * media_unit)

	if plain_region_length:
		_parse_plain_region(rom, metadata, plain_region_offset, plain_region_length)
	#Logo region: Stuff and things
	if exefs_length:
		_parse_exefs(rom, metadata, exefs_offset)
	#RomFS: Filesystem really

	if (not is_not_cxi) and is_decrypted:
		extended_header = rom.read(seek_to=offset + 0x200, amount=0x800)
		system_control_info = extended_header[0:0x200]
		#Access control info: 0x200:0x400
		#AccessDesc signature: 0x400:0x500
		#RSA-2048 public key: 0x500:0x600
		#Access control info 2: 0x600:0x800
		
		metadata.specific_info['Internal Title'] = system_control_info[0:8].decode('ascii', errors='ignore').rstrip('\0')
		#Reserved: 0x8:0xd
		#Flags (bit 0 = CompressExefsCode, bit 1 = SDApplication): 0xd
		#Remaster version: 0xe:0x10
		#Text code set info: 0x10:1c
		#Stack size: 0x1c:0x20
		#Read only code set info: 0x20:0x2c
		#Reserved: 0x2c:0x30
		#Data code set info: 0x30:0x3c
		#BSS size: 0x3c:0x40
		#Dependency module ID list: 0x40:0x1c0
		#SystemInfo: 0x1c0:0x200
		save_size = int.from_bytes(system_control_info[0x1c0:0x1c8], 'little')
		metadata.save_type = SaveType.Internal if save_size > 0 else SaveType.Nothing
		#access_control_info = extended_header[0x200:0x400]
		#arm11_local_sys_capabilities = access_control_info[0:0x170]
		#flag1 = arm11_local_sys_capabilities[0xc] Enable L2 cache, 804MHz CPU speed
		#flag2 = arm11_local_sys_capabilities[0xd] New 3DS system mode (Legacy/Prod/Dev1/Dev2)
		#flag0 = arm11_local_sys_capabilities[0xe] Ideal processor, affinity mask, Old3DS system mode (Prod/Dev1-Dev4)
		#storage_info = arm11_local_sys_capabilities[0x30:0x50]
		#service_access_control = arm11_local_sys_capabilities[0x50:0x150]
		#extended_service_access_control = arm11_local_sys_capabilities[0x150:0x160]

def _parse_plain_region(rom: FileROM, metadata: Metadata, offset: int, length: int):
	#Plain region stores the libraries used, at least for official games
	#See also: https://github.com/Zowayix/ROMniscience/wiki/3DS-libraries-used for research
	#Hmm… since I sort of abandoned ROMniscience I should put that somewhere else
	plain_region = rom.read(seek_to=offset, amount=length)
	libraries = (lib.decode('ascii', errors='backslashreplace') for lib in plain_region.split(b'\x00') if lib)

	#TODO: If a game has an update which adds functionality identified by one of these library names, then that'll be a separate file, so it's like... how do we know that Super Smash Bros the .3ds file has amiibo support when Super Smash Bros 1.1.7 update data the .cxi is where it says that, because with and only with the update data it would support amiibos, etc; if that all makes sense
	#Unless like... I search ~/.local/share/citra-emu/sdmc/Nintendo 3DS for what update CIAs are installed and... aaaaaaaaaaaaaaaa
	for library in libraries:
		if library.startswith('[SDK+ISP:QRDec'):
			metadata.specific_info['Reads QR Codes?'] = True
		elif library.startswith('[SDK+ISP:QREnc'):
			metadata.specific_info['Makes QR Codes?'] = True
		elif library == '[SDK+NINTENDO:ExtraPad]':
			metadata.specific_info['Uses Circle Pad Pro?'] = True
			#ZL + ZR + right analog stick; New 3DS has these too but the extra controls there are internally represented as a Circle Pad Pro for compatibility so this all works out I think
			inbuilt_controller = cast(input_metadata.NormalController, cast(input_metadata.CombinedController, metadata.input_info.input_options[0].inputs[0]).components[0])
			inbuilt_controller.analog_sticks += 1
			inbuilt_controller.shoulder_buttons += 2
		elif library == '[SDK+NINTENDO:Gyroscope]':
			metadata.specific_info['Uses Gyroscope?'] = True
			metadata.input_info.input_options[0].inputs.append(input_metadata.MotionControls())
		elif library == '[SDK+NINTENDO:IsRunOnSnake]':
			#There's also an IsRunOnSnakeForApplet found in some not-completely-sure-what-they-are builtin apps and amiibo Settings. Not sure if it does what I think it does
			metadata.specific_info['New 3DS Enhanced?'] = True
		elif library == '[SDK+NINTENDO:NFP]':
			metadata.specific_info['Uses Amiibo?'] = True
		elif library.startswith('[SDK+NINTENDO:CTRFaceLibrary-'):
			metadata.specific_info['Uses Miis?'] = True

def _parse_exefs(rom: FileROM, metadata: Metadata, offset: int):
	header = rom.read(seek_to=offset, amount=0x200)
	for i in range(0, 10):
		try:
			filename = header[(i * 16): (i * 16) + 8].decode('ascii').rstrip('\x00')
		except UnicodeDecodeError:
			continue
		file_offset = int.from_bytes(header[(i * 16) + 8: (i * 16) + 8 + 4], 'little') + 0x200 + offset
		file_length = int.from_bytes(header[(i * 16) + 12: (i * 16) + 12 + 4], 'little')
		if filename == 'icon':
			_parse_smdh(rom, metadata, file_offset, file_length)
		#Logo contains some stuff, banner contains 3D graphics and sounds for the home menu, .code contains actual executable


def _parse_smdh(rom: FileROM, metadata: Metadata, offset: int=0, length: int=-1):
	metadata.specific_info['Has SMDH?'] = True
	#At this point it's fine to just read in the whole thing
	smdh = rom.read(seek_to=offset, amount=length)
	_parse_smdh_data(metadata, smdh)

def _get_smdh_titles(smdh: bytes) -> tuple[Mapping[str, str], Mapping[str, str], Mapping[str, Optional[str]]]:
	short_titles: dict[str, str] = {}
	long_titles: dict[str, str] = {}
	publishers: dict[str, Optional[str]] = {}
	for i, language in languages.items():
		titles_offset = 8 + (512 * i)
		long_title_offset = titles_offset + 128
		publisher_offset = long_title_offset + 256

		try:
			short_title = smdh[titles_offset: long_title_offset].decode('utf16').rstrip('\0')
			if short_title:
				short_titles[language] = short_title
		except UnicodeDecodeError:
			pass
		try:
			long_title = smdh[long_title_offset: publisher_offset].decode('utf16').rstrip('\0')
			if long_title:
				long_titles[language] = long_title
		except UnicodeDecodeError:
			pass
		try:
			publisher = smdh[publisher_offset: publisher_offset + 0x80].decode('utf16').rstrip('\0')
			if publisher:
				while junk_suffixes.search(publisher):
					publisher = junk_suffixes.sub('', publisher)
				publishers[language] = consistentified_manufacturers.get(publisher, publisher)
		except UnicodeDecodeError:
			pass
	return short_titles, long_titles, publishers
	
def _parse_smdh_data(metadata: Metadata, smdh: bytes):
	magic = smdh[:4]
	if magic != b'SMDH':
		return
	#Version = 4-6
	#Reserved = 6-8

	parse_ratings(metadata, smdh[0x2008:0x2018], True, False)

	region_code_flag = int.from_bytes(smdh[0x2018:0x201c], 'little')
	if region_code_flag in (WiiU3DSRegionCode.RegionFree, 0xffffffff):
		region_codes = {WiiU3DSRegionCode.RegionFree}
	else:
		region_codes = set()
		for region in WiiU3DSRegionCode:
			if region in (WiiU3DSRegionCode.RegionFree, WiiU3DSRegionCode.WiiURegionFree):
				continue
			#I want a set here so this looks weird
			if region.value & region_code_flag:
				region_codes.add(region)
	if region_codes:
		metadata.specific_info['Region Code'] = region_codes
	#Match maker IDs for online play = 0x201c-0x2028
	flags = int.from_bytes(smdh[0x2028:0x202c], 'little')
	#Visible on home menu: flags & 1
	#Autoboot: flags & 2
	#Uses 3D: flags & 4 (but apparently it's more complicated than that and has more to do with parental controls)
	#Requires EULA: flags & 8
	#Autosave on exit: flags & 16
	#Uses extended banner: flags & 32
	#Region rating required: flags & 64
	#Record application usage: flags & 256 (unset on developer/customer service tools to stop them showing up in the activity log)
	#Disable SD card save backup: flags & 1024
	#has_save = (flags & 128) > 0
	#Actually just means that a warning is shown when closing, but still
	#if game.metadata.save_type == SaveType.Unknown:
	#	#I guess this'd be SaveType.MemoryCard in some cases, but... meh
	#	game.metadata.save_type = SaveType.Internal if has_save else SaveType.Nothing
	if flags & 4096:
		metadata.platform = 'New 3DS'

	#EULA version: 0x202c-0x202e
	#Reserved 2 = 0x202e-0x2030
	#Optimal animation default frame = 0x2030-0x2034
	cec_id = smdh[0x2034:0x2038]
	metadata.specific_info['Uses StreetPass?'] = cec_id != b'\x00\x00\x00\x00'
	#Reserved: 0x2038-0x2040
	
	if have_pillow:
		smol_icon = smdh[0x2040:0x24c0]
		metadata.images['Small Icon'] = _decode_icon(smol_icon, 24)

		large_icon = smdh[0x24c0:0x36c0]
		metadata.images['Icon'] = _decode_icon(large_icon, 48)

	add_info_from_local_titles(metadata, *_get_smdh_titles(smdh), region_codes)

tile_order = [
	#What the actual balls?
	0, 1, 8, 9, 2, 3, 10, 11,
	16, 17, 24, 25, 18, 19, 26, 27,
	4, 5, 12, 13, 6, 7, 14, 15,
	20, 21, 28, 29, 22, 23, 30, 31,
	32, 33, 40, 41, 34, 35, 42, 43,
	48, 49, 56, 57, 50, 51, 58, 59,
	36, 37, 44, 45, 38, 39, 46, 47,
	52, 53, 60, 61, 54, 55, 62, 63
]
def _decode_icon(icon_data: bytes, size: int) -> 'Image':
	#Assumes RGB565, which everything so far uses. Supposedly there can be other encodings, but I'll believe that when I see it
	icon = Image.new('RGB', (size, size))

	i = 0
	data = [(0, 0, 0)] * size * size
	for tile_y in range(0, size, 8):
		for tile_x in range(0, size, 8):
			for tile in range(0, 8 * 8):
				x = tile_x + (tile_order[tile] & 0b0000_0111)
				y = tile_y + ((tile_order[tile] & 0b1111_1000) >> 3)

				pixel = icon_data[i] | (icon_data[i + 1] << 8)

				blue = ((pixel >> 0) & 0b0001_1111) << 3
				green = ((pixel >> 5) & 0b0011_1111) << 2
				red = ((pixel >> 11) & 0b0001_1111) << 3

				data[y * size + x] = (red, green, blue)
				i += 2
	icon.putdata(data)
	return icon

def parse_ncsd(rom: FileROM, metadata: Metadata):
	#Assuming CCI (.3ds) here
	#Skip over SHA-256 signature and magic
	header = rom.read(seek_to=0x104, amount=0x100)
	#ROM size: 0-4
	#Media ID: 4-12
	#Partition types: 12-20
	#Partition crypt types: 20-28
	partition_offsets = []
	partition_lengths = []

	for i in range(0, 8):
		partition_offset = int.from_bytes(header[28 + (i * 4):28 + (i * 4) + 4], 'little') * media_unit
		partition_length = int.from_bytes(header[32 + (i * 4):32 + (i * 4) + 4], 'little') * media_unit
		partition_offsets.append(partition_offset)
		partition_lengths.append(partition_length)
	if partition_lengths[0]:
		#Ignore lengths, we're not just gonna read the whole NCCH in one block because that would use a heckton of memory and whatnot
		parse_ncch(rom, metadata, partition_offsets[0])
	#Partition 1: Electronic manual
	#Partition 2: Download Play child
	#Partition 6: New 3DS update data
	#Partition 7: Update data
	card_info_header = rom.read(seek_to=0x200, amount=0x314)
	card2_writeable_address = int.from_bytes(card_info_header[:4], 'little')
	if card2_writeable_address != 0xffffffff:
		metadata.save_type = SaveType.Cart
	metadata.specific_info['Title Version'] = int.from_bytes(card_info_header[0x210:0x212], 'little')
	metadata.specific_info['Card Version'] = int.from_bytes(card_info_header[0x212:0x214], 'little')

def parse_3dsx(rom: FileROM, metadata: Metadata):
	header = rom.read(amount=0x20)
	header_size = int.from_bytes(header[4:6], 'little')
	has_extended_header = header_size > 32

	look_for_smdh_file = True
	if has_extended_header:
		extended_header = rom.read(seek_to=0x20, amount=12)
		smdh_offset = int.from_bytes(extended_header[0:4], 'little')
		smdh_size = int.from_bytes(extended_header[4:8], 'little')

		if smdh_size:
			look_for_smdh_file = False
			_parse_smdh(rom, metadata, smdh_offset, smdh_size)

	if look_for_smdh_file:
		smdh_name = rom.path.with_suffix('.smdh')
		try:
			with smdh_name.open('rb') as smdh_file:
				_parse_smdh_data(metadata, smdh_file.read())
		except FileNotFoundError:
			pass

def add_3ds_metadata(game: ROMGame):
	add_3ds_system_info(game.metadata)
	if isinstance(game.rom, FileROM):
		magic = game.rom.read(seek_to=0x100, amount=4)
		#Hmm... do we really need this or should we just look at extension?
		if magic == b'NCSD':
			parse_ncsd(game.rom, game.metadata)
		elif magic == b'NCCH':
			parse_ncch(game.rom, game.metadata, 0)
		elif game.rom.extension == '3dsx':
			parse_3dsx(game.rom, game.metadata)
