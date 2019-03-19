import os
import io
import calendar

from info.region_info import TVSystem
from metadata import CPUInfo, ScreenInfo, Screen
from config import main_config

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

def parse_param_sfo(game, param_sfo):
	magic = param_sfo[:4]
	if magic != b'\x00PSF':
		return
	for key, value in convert_sfo(param_sfo).items():
		if key == 'DISC_ID':
			if value != 'UCJS10041':
				#That one's used by all the homebrews
				game.metadata.product_code = value
		elif key == 'DISC_NUMBER':
			game.metadata.specific_info['Disc-Number'] = value
		elif key == 'DISC_TOTAL':
			game.metadata.specific_info['Disc-Total'] = value
		elif key == 'TITLE':
			if game.rom.extension == 'pbp':
				game.rom.name = value
		elif key == 'PARENTAL_LEVEL':
			#According to PSDevWiki: 1 = all ages, 5 = 12+, 7 = 15+, 9 = 18+
			#There would be additional levels not mentioned here: Go! Explore (Europe) = 2; Danganronpa = 8; have heard it maxes out at 11
			if value >= 9:
				game.metadata.nsfw = True
		elif key in ('APP_VER', 'BOOTABLE', 'CATEGORY', 'DISC_VERSION', 'MEMSIZE', 'PSP_SYSTEM_VER', 'REGION', 'USE_USB'):
			#These are known, but not necessarily useful to us or we just don't feel like putting it in the metadata or otherwise doing anything with it at this point
			#APP_VER: ??? not sure how it's different from DISC_VER also seems to be 01.00
			#BOOTABLE: Should always be 1, I would think
			#Category is like "Memory stick game" "Update" "PS1 Classics", see ROMniscience notes
			#DISC_VERSION: Version number (e.g. 1.00, 1.01); must be important because Redump and No-Intro put it in the filename
			#MEMSIZE: 1 if game uses extra RAM?
			#PSP_SYSTEM_VER: Required PSP firmware version
			#REGION: Seems to always be 32768 (is anything region locked?)
			#USE_USB: ??? USB access? Official stuff seems to have this and sets it to 0
			pass
		else:
			#ATTRIBUTE: Some weird flags (see ROMniscience)
			#HRKGMP_VER = ??? (19)
			if main_config.debug:
				print(game.rom.path, 'has unknown param.sfo value', key, value)

def add_info_from_pbp(game, pbp_file):
	magic = pbp_file[:4]
	if magic != b'\x00PBP':
		#You have the occasional b'\x7ELF' here
		return
	#Unknown (some kind of version number?) 4:8
	param_sfo_offset = int.from_bytes(pbp_file[8:12], 'little') #Apparently should always be 0x28 (this would be after all these offsets)
	icon0_offset = int.from_bytes(pbp_file[12:16], 'little')
	icon1_offset = int.from_bytes(pbp_file[16:20], 'little')
	#PIC0.PNG offset: 20:24
	#PIC1.PNG offset: 24:28 #Used as background image I think
	#SND0.AT3 offset: 28:32
	#DATA.PSP offset: 32:36
	#DATA.PSAR offset: 36:40
	#These embedded files are supposedly always in this order, so you get the size by getting the difference between that file's offset and the next one (or the end of the file if it's the last one)
	if param_sfo_offset > 0x24:
		param_sfo = pbp_file[param_sfo_offset:icon0_offset]
		parse_param_sfo(game, param_sfo)
	if have_pillow:
		if icon0_offset > param_sfo_offset:
			bitmap_data = pbp_file[icon0_offset:icon1_offset]
			bitmap_data_io = io.BytesIO(bitmap_data)
			game.metadata.images['Banner'] = Image.open(bitmap_data_io)
		#There's icon1 as well but I'm not sure of the difference or if that's used and I'll do something about that later I guess

def add_psp_system_info(game):
	cpu_info = CPUInfo()
	cpu_info.main_cpu = 'Sony CXD2962GG'
	cpu_info.clock_speed = 333 * 1000 * 1000
	game.metadata.cpu_info = cpu_info

	screen = Screen()
	screen.width = 480
	screen.height = 272
	screen.type = 'lcd'
	screen.tag = 'screen'
	screen.refresh_rate = 60  #I presume so, anyway... good luck finding actual information. I bet it's not really exactly 60Hz

	screen_info = ScreenInfo()
	screen_info.screens = [screen]
	game.metadata.screen_info = screen_info

def add_psp_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	add_psp_system_info(game)

	if game.rom.extension == 'pbp':
		#These are basically always named EBOOT.PBP (due to how PSPs work I guess), so that's not a very good launcher name, and use the folder it's stored in instead
		game.rom.name = os.path.basename(game.folder)
		add_info_from_pbp(game, game.rom.read())
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
				parse_param_sfo(game, param_sfo_buf.getvalue())
			except PyCdlibInvalidInput:
				if main_config.debug:
					print(game.rom.path, 'has no PARAM.SFO inside')
			if have_pillow:
				icon0_buf = io.BytesIO()
				try:
					iso.get_file_from_iso_fp(icon0_buf, iso_path='/PSP_GAME/ICON0.PNG')
					game.metadata.images['Banner'] = Image.open(icon0_buf)
				except PyCdlibInvalidInput:
					pass
		except PyCdlibInvalidISO as ex:
			if main_config.debug:
				print(game.rom.path, 'is invalid ISO', ex)
		except struct.error as ex:
			print(game.rom.path, 'is invalid ISO and has some struct.error', ex)
