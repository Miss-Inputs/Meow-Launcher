import calendar
import io
import os
import re

import input_metadata
from common_types import MediaType
from config.main_config import main_config

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

try:
	from pycdlib import PyCdlib
	from pycdlib.pycdlibexception import PyCdlibInvalidISO, PyCdlibInvalidInput
	import struct #To handle struct.error
	have_pycdlib = True
except ModuleNotFoundError:
	have_pycdlib = False

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

valid_product_code = re.compile(r'^\w{4}\d{5}$')

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

def load_image_from_bytes(data):
	bitmap_data_io = io.BytesIO(data)
	try:
		image = Image.open(bitmap_data_io)
		return image
	#except (OSError, SyntaxError):
	except OSError:
		#Why is it SyntaxError though? Agggggh
		return None

def add_info_from_pbp(rom, metadata, pbp_file):
	magic = pbp_file[:4]
	if magic != b'\x00PBP':
		#You have the occasional b'\x7ELF' here
		return
	#Unknown (some kind of version number?) 4:8
	param_sfo_offset = int.from_bytes(pbp_file[8:12], 'little') #Apparently should always be 0x28 (this would be after all these offsets)
	icon0_offset = int.from_bytes(pbp_file[12:16], 'little')
	icon1_offset = int.from_bytes(pbp_file[16:20], 'little') #Animated?
	pic0_offset = int.from_bytes(pbp_file[20:24], 'little')
	pic1_offset = int.from_bytes(pbp_file[24:28], 'little') #Used as background image?
	snd0_offset = int.from_bytes(pbp_file[28:32], 'little') #.at3 file, who knows what we would do with this
	#DATA.PSP offset: 32:36
	#DATA.PSAR offset: 36:40
	#These embedded files are supposedly always in this order, so you get the size by getting the difference between that file's offset and the next one (or the end of the file if it's the last one)
	if param_sfo_offset > 0x24:
		param_sfo = pbp_file[param_sfo_offset:icon0_offset]
		parse_param_sfo(rom, metadata, param_sfo)
	if have_pillow:
		if icon0_offset > param_sfo_offset:
			banner = load_image_from_bytes(pbp_file[icon0_offset:icon1_offset])
			if banner:
				metadata.images['Banner'] = banner
		if icon1_offset > icon0_offset:
			#Dunno what these 3 other images do exactly, so they have crap names for now
			icon1 = load_image_from_bytes(pbp_file[icon1_offset:pic0_offset])
			if icon1:
				metadata.images['Icon-1'] = icon1
		if pic0_offset > icon1_offset:
			pic0 = load_image_from_bytes(pbp_file[pic0_offset:pic1_offset])
			if pic0:
				metadata.images['Picture-0'] = pic0
		if pic1_offset > pic0_offset:
			pic1 = load_image_from_bytes(pbp_file[pic1_offset:snd0_offset])
			if pic1:
				metadata.images['Background-Image'] = pic1

def add_psp_system_info(metadata):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.analog_sticks = 1
	builtin_gamepad.face_buttons = 4 #also Start, Select
	builtin_gamepad.shoulder_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)

def parse_product_code(metadata):
	value = metadata.product_code
	if valid_product_code.fullmatch(value):
		if value[0] == 'U':
			#Physical media (U specifically is PSP UMD)
			if value[1] == 'C':
				#(C)opyrighted by Sony as opposed to (L)icensed to Sony
				#value[2] would indicate a specific branch of Sony (P = Japan PS1/PS2)
				metadata.publisher = 'Sony'
		elif value.startswith('NP'):
			#Digital release
			metadata.media_type = MediaType.Digital
			if value[3] in ('A', 'C', 'F', 'G', 'I', 'K', 'W', 'X', 'Y', 'Z'):
				metadata.publisher = 'Sony'

def get_image_from_iso(iso, path):
	buf = io.BytesIO()
	try:
		iso.get_file_from_iso_fp(buf, iso_path=path)
		clone = io.BytesIO(buf.getvalue()) #Pillow insists on closing the stream to use .verify()
		try:
			image = Image.open(clone)
			image.verify()
		except (OSError, SyntaxError):
			return None
		return Image.open(buf)
	except PyCdlibInvalidInput:
		pass

def add_psp_metadata(game):
	add_psp_system_info(game.metadata)

	if game.rom.extension == 'pbp':
		game.metadata.categories = game.metadata.categories[:-1]
		add_info_from_pbp(game.rom, game.metadata, game.rom.read())
		#These are basically always named EBOOT.PBP (due to how PSPs work I guess), so that's not a very good launcher name, and use the folder it's stored in instead
		if game.rom.name.lower() == 'eboot':
			game.metadata.add_alternate_name(os.path.basename(os.path.dirname(game.rom.path)), 'Folder-Name')
			game.rom.ignore_name = True
	elif game.rom.extension == 'iso' and have_pycdlib:
		iso = PyCdlib()
		try:
			iso.open(game.rom.path)
			param_sfo_buf = io.BytesIO()				

			try:
				iso.get_file_from_iso_fp(param_sfo_buf, iso_path='/PSP_GAME/PARAM.SFO')
				date = iso.get_record(iso_path='/PSP_GAME/PARAM.SFO').date
				#This would be more like a build date (seems to be the same across all files) rather than the release date, but it seems to be close enough
				game.metadata.year = date.years_since_1900 + 1900
				game.metadata.month = calendar.month_name[date.month]
				game.metadata.day = date.day_of_month
				parse_param_sfo(game.rom, game.metadata, param_sfo_buf.getvalue())
			except PyCdlibInvalidInput:
				try:
					iso.get_record(iso_path='/UMD_VIDEO/PARAM.SFO')
					#We could parse this PARAM.SFO but there's not much point given we aren't going to make a launcher for UMD videos at this stage
					#TODO There is also potentially /UMD_AUDIO/ I think too so I should rewrite this one day
					game.metadata.specific_info['Is-UMD-Video'] = True
					return
				except PyCdlibInvalidInput:
					if main_config.debug:
						print(game.rom.path, 'has no PARAM.SFO inside')
			if have_pillow:
				game.metadata.images['Banner'] = get_image_from_iso(iso, '/PSP_GAME/ICON0.PNG')
				game.metadata.images['Icon-1'] = get_image_from_iso(iso, '/PSP_GAME/ICON1.PNG')
				game.metadata.images['Picture-0'] = get_image_from_iso(iso, '/PSP_GAME/PIC0.PNG')
				game.metadata.images['Background-Image'] = get_image_from_iso(iso, '/PSP_GAME/PIC1.PNG')
		except PyCdlibInvalidISO as ex:
			if main_config.debug:
				print(game.rom.path, 'is invalid ISO', ex)
		except struct.error as ex:
			print(game.rom.path, 'is invalid ISO and has some struct.error', ex)

	#https://www.psdevwiki.com/ps3/Productcode#Physical
	if game.metadata.product_code:
		parse_product_code(game.metadata)
