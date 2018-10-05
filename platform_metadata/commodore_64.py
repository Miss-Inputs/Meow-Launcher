from software_list_info import get_software_list_entry, find_in_software_lists, get_crc32_for_software_list

def add_commodore_64_metadata(game):
	header = game.rom.read(amount=64)
	magic = header[:16]
	if magic == b'C64 CARTRIDGE   ':
		headered = True
		cart_type = int.from_bytes(header[22:24], 'big')
		game.metadata.specific_info['Cart-Type'] = cart_type
		if cart_type == 15:
			game.metadata.platform = 'C64GS'
	else:
		headered = False

	game.metadata.specific_info['Headered'] = headered

	if headered:
		software = None
		#Skip CRT header
		data = game.rom.read(seek_to=64)

		total_data = b''
		i = 0
		while i < len(data):
			chip_header = data[i:i+16]
			total_size = int.from_bytes(chip_header[4:8], 'big')
			chip_size = int.from_bytes(chip_header[14:16], 'big')
			total_data += data[i+16:i+16+chip_size]
			i += total_size

		crc = get_crc32_for_software_list(total_data)
		software = find_in_software_lists(game.software_lists, crc=crc)
	else:
		software = get_software_list_entry(game)

	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')
		#There's dataarea nvram, but those are two carts which are more accurately described as device BIOSes, so I won't bother
