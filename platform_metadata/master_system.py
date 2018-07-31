import calendar

def decode_bcd(i):
	if not isinstance(i, int):
		return (decode_bcd(i[1]) * 100) + decode_bcd(i[0])

	hi = (i & 0xf0) >> 4
	lo = i & 0x0f
	return (hi * 10) + lo

def parse_sdsc_header(game, header):
	#Minor version: header[0]
	#Major version: header[1]

	day = decode_bcd(header[2])
	month = decode_bcd(header[3])
	year = decode_bcd(header[4:6])
	if day >= 1 and day <= 31:
		game.metadata.day = day
	if month >= 1 and month <= 12:
		game.metadata.month = calendar.month_name[month]
	if year:
		game.metadata.year = year

	author_offset = int.from_bytes(header[6:8], 'little')
	#Name offset: header[8:10]
	#Description offset: header[10:12]
	if author_offset > 0 and author_offset < 0xffff:
		#Assume sane maximum of 255 chars
		try:
			game.metadata.developer = game.rom.read(seek_to=author_offset, amount=255).partition(b'\x00')[0].decode('ascii')
		except UnicodeDecodeError:
			pass
		

def get_sms_metadata(game):
	sdsc_header = game.rom.read(seek_to=0x7fe0, amount=12)
	if sdsc_header[:4] == b'SDSC':
		parse_sdsc_header(game, sdsc_header[4:])