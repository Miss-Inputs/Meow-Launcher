import os
import io

from info.region_info import TVSystem
from metadata import CPUInfo, ScreenInfo, Screen
from config import main_config

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

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
		elif key in ('DISC_VERSION', 'PSP_SYSTEM_VER', 'REGION', 'BOOTABLE', 'PARENTAL_LEVEL', 'CATEGORY', 'MEMSIZE', 'ATTRIBUTE'):
			#These are known, but not necessarily useful to us or we just don't feel like putting it in the metadata or otherwise doing anything with it at this point
			#TODO: Make use of region on retail discs, appears to be some kind of bitmask, it's 32768 on homebrew
			#Noted fields from ROMniscience:
			#ACCOUNT_ID: ???
			#ANALOG_MDOE: ???
			#APP_VER: ??? not sure how it's different from DISC_VER
			#USE_USB: ??? USB access? Championship Manager 2010 beta has this
			#PSP_SYSTEM_VER: Required PSP firmware version?
			#DISC_VER: Version number (e.g. 1.00)
			#Category is like "Memory stick game" "Update" "PS1 Classics", see ROMniscience notes
			#Memsize = 1 if the game uses extra RAM?
			#Attribute: Bitmask flags of some weird stuff
			#PARENTAL_LEVEL: Parental controls level
			pass
		else:
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
			#TODO: Use as banner instead if it's the wrong aspect ratio
			game.icon = Image.open(bitmap_data_io)
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
	#TODO: Get stuff out of .iso files (they are standard ISO9660 and should have an EBOOT.PBP file somewhere inside)
