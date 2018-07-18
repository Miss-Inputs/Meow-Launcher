from common import convert_alphanumeric, NotAlphanumericException
from metadata import SaveType
from info.region_info import TVSystem
from platform_metadata.nintendo_common import nintendo_licensee_codes

def add_n64_metadata(game):
	header = game.rom.read(amount=64)
	magic = header[:4]
	if magic == b'\x80\x37\x12\x40':
		#Z64
		#TODO: Detect format and add as metadata. This'll be useful because some emulators won't even try and launch the thing if the first four bytes don't match something expected, even if it is a raw non-swapped dump that just happens to have weird values there
		try:
			product_code = convert_alphanumeric(header[59:63])
			game.metadata.specific_info['Product-Code'] = product_code
		except NotAlphanumericException:
			pass
		

