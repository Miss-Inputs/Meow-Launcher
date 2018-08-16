import calendar

from metadata import SaveType
from .nintendo_common import nintendo_licensee_codes

def decode_bcd(i):
	hi = (i & 0xf0) >> 4
	lo = i & 0x0f
	return (hi * 10) + lo

def add_nes_metadata(game):
	if game.rom.extension == 'fds':
		game.metadata.platform = 'FDS'
		header = game.rom.read(amount=56)
		if header[:4] == b'FDS\x1a':
			header = game.rom.read(seek_to=16, amount=56)

		licensee_code = '{:02X}'.format(header[15])
		if licensee_code in nintendo_licensee_codes:
			game.metadata.publisher = nintendo_licensee_codes[licensee_code]
		
		game.metadata.revision = header[20]
		#Uses Showa years (hence 1925), in theory... but then some disks (notably Zelda) seem to use 19xx years, as it has an actual value of 0x86 which results in it being Showa 86 = 2011, but it should be [Feb 21] 1986, so... hmm
		year = decode_bcd(header[31])
		if year >= 61 and year <= 99: #Showa 61 = 1986 when the FDS was released. Year > 99 wouldn't be valid BCD, so... I'll check back in 2025 to see if anyone's written homebrew for the FDS in that year and then I'll figure out what I'm doing. But homebrew right now seems to leave the year as 00 anyway, though
			year = 1925 + year
			game.metadata.year = year
		month = decode_bcd(header[32])
		if month >= 1 and month <= 12:
			game.metadata.month = calendar.month_name[month]
		day = decode_bcd(header[33])
		if day >= 1 and day <= 28:
			game.metadata.day = day

	else:
		header = game.rom.read(amount=16)
		magic = header[:4]
		if magic == b'NES\x00' or magic == b'NES\x1a':
			game.metadata.specific_info['Headered'] = False
			#Some emulators are okay with not having a header if they have something like an internal database, others are not.
			#Note that \x00 at the end instead of \x1a indicates this is actually Wii U VC, but it's still the same header format
			flags = header[6]
			has_battery = (flags & 2) > 0
			game.metadata.save_type = SaveType.Cart if has_battery else SaveType.Nothing

			more_flags = header[7]
			if more_flags & 1:
				game.metadata.platform = 'VS Unisystem'
			elif more_flags & 2:
				game.metadata.platform = 'PlayChoice-10'
			
			#Could get the mapper here, I suppose, but then it gets tricky when you involve NES 2.0 (which has the same header format for the first few bytes)
			#TV type apparently isn't used much despite it being part of the iNES specification, and looking at a lot of headered ROMs it does seem that they are all NTSC other than a few that say PAL that shouldn't be, so yeah, I wouldn't rely on it. Might as well just use the filename.
		else:
			game.metadata.specific_info['Headered'] = False
