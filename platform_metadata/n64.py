from common import convert_alphanumeric, NotAlphanumericException

def add_n64_metadata(game):
	header = game.rom.read(amount=64)
	magic = header[:4]
	if magic == b'\x80\x37\x12\x40':
		#Z64
		#TODO: Detect format and add as metadata. This'll be useful because some emulators won't even try and launch the thing if the first four bytes don't match something expected, even if it is a raw non-swapped dump that just happens to have weird values there
		#TODO: Check Mupen64Plus's database (/usr/local/share/mupen64plus/mupen64plus.ini). That will take 5 hours because it's indexed by MD5 and not something like internal name or product code, but eh... it has the things. For ROMs it knows about. Hmm. I guess it's all we can do, unless you want to make a whole database of N64 ROMs yourself, young lady.
		try:
			product_code = convert_alphanumeric(header[59:63])
			game.metadata.specific_info['Product-Code'] = product_code
		except NotAlphanumericException:
			pass
		
