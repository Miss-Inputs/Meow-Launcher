from config.main_config import main_config

def convert_sfo(sfo):
	d = {}
	#This is some weird key value format thingy
	key_table_start = int.from_bytes(sfo[8:12], 'little')
	data_table_start = int.from_bytes(sfo[12:16], 'little')
	number_of_entries = int.from_bytes(sfo[16:20], 'little')

	for i in range(0, number_of_entries * 16, 16):
		kv = sfo[20 + i:20 + i + 16]
		key_offset = key_table_start + int.from_bytes(kv[0:2], 'little')
		data_format = int.from_bytes(kv[2:4], 'little')
		data_used_length = int.from_bytes(kv[4:8], 'little')
		#data_total_length = int.from_bytes(kv[8:12], 'little') #Not sure what that would be used for
		data_offset = data_table_start + int.from_bytes(kv[12:16], 'little')

		key = sfo[key_offset:].split(b'\x00', 1)[0].decode('utf8', errors='ignore')

		value = None
		if data_format == 4: #UTF8 not null terminated
			value = sfo[data_offset:data_offset+data_used_length, 'little'].decode('utf8', errors='ignore')
		elif data_format == 0x204: #UTF8 null terminated
			value = sfo[data_offset:].split(b'\x00', 1)[0].decode('utf8', errors='ignore')
		elif data_format == 0x404: #int32
			value = int.from_bytes(sfo[data_offset:data_offset+4], 'little')
		else:
			#Whoops unknown format
			continue

		d[key] = value
	return d

def parse_param_sfo(rom, metadata, param_sfo):
	magic = param_sfo[:4]
	if magic != b'\x00PSF':
		return
	for key, value in convert_sfo(param_sfo).items():
		if key == 'DISC_ID':
			if value != 'UCJS10041':
				#That one's used by all the homebrews
				metadata.product_code = value
		elif key == 'DISC_NUMBER':
			metadata.disc_number = value
		elif key == 'DISC_TOTAL':
			metadata.disc_total = value
		elif key == 'TITLE':
			metadata.add_alternate_name(value, 'Banner-Title')
		elif key == 'PARENTAL_LEVEL':
			#Seems this doesn't actually mean anything by itself, and is Sony's own rating system, so don't try and think about it too much
			metadata.specific_info['Parental-Level'] = value
		elif key == 'CATEGORY':
			#This is a two letter code which generally means something like "Memory stick game" "Update" "PS1 Classics", see ROMniscience notes
			if value == 'UV':
				metadata.specific_info['Is-UMD-Video'] = True
		elif key == 'DISC_VERSION':
			if value[0] != 'v':
				value = 'v' + value
			metadata.specific_info['Version'] = value
		elif key in ('APP_VER', 'BOOTABLE', 'MEMSIZE', 'PSP_SYSTEM_VER', 'REGION', 'USE_USB', 'ATTRIBUTE', 'HRKGMP_VER'):
			#These are known, but not necessarily useful to us or we just don't feel like putting it in the metadata or otherwise doing anything with it at this point
			#APP_VER: ??? not sure how it's different from DISC_VERSION also seems to be 01.00
			#BOOTABLE: Should always be 1, I would think
			#MEMSIZE: 1 if game uses extra RAM?
			#PSP_SYSTEM_VER: Required PSP firmware version
			#REGION: Seems to always be 32768 (is anything region locked?)
			#USE_USB: ??? USB access? Official stuff seems to have this and sets it to 0
			#ATTRIBUTE: Some weird flags (see ROMniscience)
			#HRKGMP_VER = ??? (19)
			pass
		else:
			if main_config.debug:
				print(rom.path, 'has unknown param.sfo value', key, value)
