from software_list_info import get_software_list_entry

def add_uzebox_metadata(game):
	#Input info: SNES controllers, but that could be any SNES peripheral (mouse, etc)
	#TV system: ??? maybe agnostic in this day and age?
	#Save type: ????

	header = game.rom.read(amount=512)
	magic = header[0:6]
	if magic != b'UZEBOX':
		has_header = False
	else:
		has_header = True
		#Header version: 6
		#Target: 7 (0 = ATmega644, 1 = reserved for ATmega1284)
		#Program size: 8-0xc (LE)
		game.metadata.year = int.from_bytes(header[0xc:0xe], 'little')
		#Name: 0xe:0x2e
		game.metadata.developer = game.metadata.publisher = header[0x2e:0x4e].decode('ascii', errors='backslashreplace').rstrip('\0')
		#Icon (sadly unused): 0x4e:0x14e
		#CRC32: 0x14e:0x152
		game.metadata.specific_info['Uses-Mouse'] = header[0x152] == 1
		#Description (unused): 0x153:0x193
	game.metadata.specific_info['Headered'] = has_header

	software = get_software_list_entry(game, 512 if has_header else 0)
	if software:
		software.add_generic_info(game)
		if game.metadata.publisher == 'Belogic':
			#Belogic just make the console itself, but don't actually make games necessarily
			game.metadata.publisher = game.metadata.developer
		game.metadata.product_code = software.get_info('serial')
