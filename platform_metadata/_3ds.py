
from info.region_info import TVSystem
from metadata import CPUInfo, ScreenInfo, Screen, SaveType
from common import convert_alphanumeric, NotAlphanumericException
from .nintendo_common import nintendo_licensee_codes

def add_3ds_system_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

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

media_unit = 0x200

def parse_ncch(game, offset):
	#Skip over SHA-256 siggy and magic
	header = game.rom.read(seek_to=offset + 0x104, amount=0x100)
	#Content size: 0-4 (media unit)
	#Partition ID: 4-12
	try:
		maker = convert_alphanumeric(header[12:14])
		if maker in nintendo_licensee_codes:
			game.metadata.publisher = nintendo_licensee_codes[maker]
	except NotAlphanumericException:
		pass
	#NCCH version: 14-16 (always 2?)
	game.metadata.specific_info['NCCH-Version'] = int.from_bytes(header[14:16], 'little')
	#Something about a hash: 16-20
	#Program ID: 20-28
	#Reserved: 28-44
	#Logo region hash: 44-76
	try:
		product_code = header[76:86].decode('ascii')
		game.metadata.specific_info['Product-Code'] = product_code
		#As usual, can get country and type from here, but it has more letters and as such you can also get category as well, or like... type 2 electric boogaloo. This also means we can't use convert_alphanumeric because it contains dashes, so I guess I need to fiddle with that method if I want to use it like that
		#(To be precise: P = retail/cart, N = digital only, M = DLC, T = demos, U = patches)
		#Should ignore everything if it's CTR-P-CTAP
	except UnicodeDecodeError:
		pass
	#Extended header hash: 92-124
	#Extended header size: 124-128
	#Reserved: 128-132
	flags = header[132:140]
	is_data = (flags[5] & 1) > 0
	is_executable = (flags[5] & 2) > 0
	is_not_cxi = is_data and not is_executable
	game.metadata.specific_info['Is-CXI'] = not is_not_cxi
	#Is system update = flags[5] & 4
	#Is electronic manual = flags[5] & 8
	#Is trial = flags[5] & 16
	#Is zero key encrypted = flags[7] & 1
	is_decrypted = (flags[7] & 4) > 0
	game.metadata.specific_info['Decrypted'] = is_decrypted

	plain_region_offset = (int.from_bytes(header[140:144], 'little') * media_unit) + offset
	plain_region_length = (int.from_bytes(header[144:148], 'little') * media_unit)
	#logo_region_offset = (int.from_bytes(header[148:152], 'little') * media_unit) + offset
	#logo_region_length = (int.from_bytes(header[152:156], 'little') * media_unit)
	exefs_offset = (int.from_bytes(header[156:160], 'little') * media_unit) + offset
	exefs_length = (int.from_bytes(header[160:164], 'little') * media_unit)
	#romfs_offset = (int.from_bytes(header[164:168], 'little') * media_unit) + offset
	#romfs_length = (int.from_bytes(header[168:172], 'little') * media_unit)

	if plain_region_length:
		parse_plain_region(game, plain_region_offset, plain_region_length)
	#Logo region: Stuff and things
	if exefs_length:
		parse_exefs(game, exefs_offset)
	#RomFS: Filesystem really

	#Don't really need extended header, it's at offset + 0x200 if CXI and decrypted

def parse_plain_region(game, offset, length):
	#Plain region contains libraries used and such, it's pretty dang cool actually and could be useful here but also mysterious
	plain_region = game.rom.read(seek_to=offset, amount=length)
	game.metadata.specific_info['Libraries'] = [lib.decode('ascii', errors='backslashreplace') for lib in plain_region.split(b'\x00') if lib]

def parse_exefs(game, offset):
	header = game.rom.read(seek_to=offset, amount=0x200)
	for i in range(0, 10):
		try:
			filename = header[(i * 16): (i * 16) + 8].decode('ascii').rstrip('\x00')
		except UnicodeDecodeError:
			continue
		file_offset = int.from_bytes(header[(i * 16) + 8: (i * 16) + 8 + 4], 'little') + 0x200 + offset
		file_length = int.from_bytes(header[(i * 16) + 12: (i * 16) + 12 + 4], 'little')
		if filename == 'icon':
			parse_smdh(game, file_offset, file_length)
		#Logo contains some stuff, banner contains 3D graphics and sounds for the home menu, .code contains actual executable
		
def parse_smdh(game, offset=0, length=-1):
	#At this point it's fine to just read in the whole thing
	smdh = game.rom.read(seek_to=offset, amount=length)
	#Magic = 0-4
	magic = smdh[:4]
	if magic != b'SMDH':
		return
	#Version = 4-6
	#Reserved = 6-8
	#Titles = 8-0x2008 (512 bytes each (128 short title + 256 long title + 128 publisher ) * 16 languages)
	#Is it always the publisher? Can I trust that information for ze metadatum?
	#Ratings = 0x2008-0x2018 (mostly same format as DSi and Wii but not quite)
	#Region coding = 0x2018-0x201c
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
	has_save = (flags & 128) > 0
	#Actually just means that a warning is shown when closing, but still
	if game.metadata.save_type == SaveType.Unknown:
		#TODO: Should this be SaveType.MemoryCard in some cases?
		game.metadata.save_type = SaveType.Internal if has_save else SaveType.Nothing
	if flags & 4096:
		game.metadata.platform = 'New 3DS'	

	#EULA version: 0x202c-0x202e
	#Reserved 2 = 0x202e-0x2030
	#Optimal animation default frame = 0x2030-0x2034
	#CEC: 0x2034-0x2038
	#Reserved: 0x2038-0x2040
	#Smol icon (24x24): 0x2040-0x24c0
	#Large icon (48x48): 0x24c0-0x36c0

def parse_ncsd(game):
	#Assuming CCI (.3ds) here
	#Skip over SHA-256 signature and magic
	header = game.rom.read(seek_to=0x104, amount=0x100)
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
		parse_ncch(game, partition_offsets[0])
	#Partition 1: Electronic manual
	#Partition 2: Download Play child
	#Partition 6: New 3DS update data
	#Partition 7: Update data
	card_info_header = game.rom.read(seek_to=0x200, amount=0x314)
	card2_writeable_address = int.from_bytes(card_info_header[:4], 'little')
	if card2_writeable_address != 0xffffffff:
		game.metadata.save_type = SaveType.Cart
	game.metadata.specific_info['Title-Version'] = int.from_bytes(card_info_header[0x210:0x212], 'little')
	game.metadata.specific_info['Card-Version'] = int.from_bytes(card_info_header[0x212:0x214], 'little')

def add_3ds_metadata(game):
	add_3ds_system_info(game)
	magic = game.rom.read(seek_to=0x100, amount=4)
	#Hmm... do we really need this or should we just look at extension?
	if magic == b'NCSD':
		parse_ncsd(game)
	elif magic == b'NCCH':
		parse_ncch(game, 0)
	elif game.rom.extension == '3dsx':
		#TODO Really just to check if there's an embedded SMDH, or to look for a sibling SMDH
		pass
