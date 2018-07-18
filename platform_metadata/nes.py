import os

from metadata import SaveType
from info.region_info import TVSystem
from metadata import SaveType, CPUInfo, ScreenInfo, Screen
from common import convert_alphanumeric, NotAlphanumericException
from platform_metadata.nintendo_common import nintendo_licensee_codes

def decode_bcd(i):
	hi = (i & 0xf0) >> 4
	lo = i & 0x0f
	return (hi * 10) + lo

def add_nes_metadata(game):
	if game.rom.extension == 'fds':
		game.metadata.platform = 'FDS'
		header = game.rom.read(amount=56)
		licensee_code = '{:02X}'.format(header[15])
		if licensee_code in nintendo_licensee_codes:
			game.metadata.author = nintendo_licensee_codes[licensee_code]
		
		#Uses Showa years (hence 1925), in theory... but then some disks (notably Zelda) seem to use 19xx years, as it has an actual value of 0x86 which results in it being Showa 86 = 2011, but it should be [Feb 21] 1986, so... hmm. I guess I could say anything after the Showa perioud (1989) is just plain years? Who's out there developing homebrew in the new millenium anyway
		game.metadata.year = 1925 + decode_bcd(header[31])
	else:
		header = game.rom.read(amount=16)
		magic = header[:4]
		if magic == b'NES\x00' or magic == b'NES\x1a':
			game.metadata.specific_info['Headered'] = False
			#Some emulators are okay with not having a header if they have something like an internal database, others are not.
			#Note that \x00 at the end instead of \x1a indicates this is actually Wii U VC, but it's still the same header format
			flags = header[7]
			has_battery = (flags & 2) > 0
			game.metadata.save_type = SaveType.Cart if has_battery else SaveType.Nothing
			
			#Could get the mapper here, I suppose, but then it gets tricky when you involve NES 2.0 (which has the same header format for the first few bytes)
			#TV type apparently isn't used much despite it being part of the iNES specification, and looking at a lot of headered ROMs it does seem that they are all NTSC other than a few that say PAL that shouldn't be, so yeah, I wouldn't rely on it. Might as well just use the filename.
		else:
			game.metadata.specific_info['Headered'] = False
