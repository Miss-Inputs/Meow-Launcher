from common import convert_alphanumeric, NotAlphanumericException
from software_list_info import get_software_list_entry

def add_n64_metadata(game):
	header = game.rom.read(amount=64)
	magic = header[:4]
	if magic == b'\x80\x37\x12\x40':
		#Z64
		#TODO: Detect format and add as metadata. This'll be useful because some emulators won't even try and launch the thing if the first four bytes don't match something expected, even if it is a raw non-swapped dump that just happens to have weird values there
		#TODO: Check Mupen64Plus's database (/usr/local/share/mupen64plus/mupen64plus.ini). That will take 5 hours because it's indexed by MD5 and not something like internal name or product code, but eh... it has the things. For ROMs it knows about. Hmm. I guess it's all we can do, unless you want to make a whole database of N64 ROMs yourself, young lady.
		#TODO: If v64, put the endian down, flip it and reverse it
		try:
			product_code = convert_alphanumeric(header[59:63])
			game.metadata.product_code = product_code
		except NotAlphanumericException:
			pass
		game.metadata.revision = header[63]

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		if not game.metadata.product_code:
			game.metadata.product_code = software.get_info('serial')
