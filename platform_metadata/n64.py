import zlib

from common import convert_alphanumeric, NotAlphanumericException
from software_list_info import find_in_software_lists

def _byteswap(b):
	byte_array = bytearray(b)
	for i in range(0, len(byte_array), 2):
		temp = byte_array[i]
		byte_array[i] = byte_array[i + 1]
		byte_array[i + 1] = temp
	return bytes(byte_array)

def add_n64_metadata(game):
	entire_rom = game.rom.read()
	
	magic = entire_rom[:4]

	byte_swap = False
	header = entire_rom[:64]
	if magic == b'\x80\x37\x12\x40':
		game.metadata.specific_info['ROM-Format'] = 'Z64'
	elif magic == b'\x37\x80\x40\x12':
		byte_swap = True
		game.metadata.specific_info['ROM-Format'] = 'V64'
	else:
		#TODO: Detect other formats (there are a few homebrews that start with 0x80 0x37 but not 0x12 0x40 after that
		game.metadata.specific_info['ROM-Format'] = 'Unknown'
		return

	#TODO: Check Mupen64Plus's database (/usr/local/share/mupen64plus/mupen64plus.ini). That will take 5 hours because it's indexed by MD5 and not something like internal name or product code, but eh... it has the things. For ROMs it knows about. Hmm. I guess it's all we can do, unless you want to make a whole database of N64 ROMs yourself, young lady.

	if byte_swap:
		header = _byteswap(header)
	try:
		product_code = convert_alphanumeric(header[59:63])
		game.metadata.product_code = product_code
	except NotAlphanumericException:
		pass
	game.metadata.revision = header[63]

	if not byte_swap:
		entire_rom = _byteswap(entire_rom)
		#For some reason, MAME uses little endian dumps in its software list at the moment, hence "not byte_swap" which would be wrong otherwise

	rom_crc32 = '{:08x}'.format(zlib.crc32(entire_rom))

	software = find_in_software_lists(game.software_lists, crc=rom_crc32)
	if software:
		software.add_generic_info(game)
		if not game.metadata.product_code:
			game.metadata.product_code = software.get_info('serial')
