import io
import os
from typing import Optional, cast

from meowlauncher import input_metadata
from meowlauncher.config.main_config import main_config
from meowlauncher.games.roms.rom import ROM, FileROM
from meowlauncher.games.roms.rom_game import ROMGame
from meowlauncher.metadata import Date, Metadata

from .common.playstation_common import parse_param_sfo, parse_product_code

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

try:
	import struct  # To handle struct.error

	from pycdlib import PyCdlib
	from pycdlib.pycdlibexception import PyCdlibInvalidInput, PyCdlibInvalidISO
	have_pycdlib = True
except ModuleNotFoundError:
	have_pycdlib = False

def load_image_from_bytes(data: bytes) -> Optional['Image.Image']:
	bitmap_data_io = io.BytesIO(data)
	try:
		image = Image.open(bitmap_data_io)
		return image
	except OSError:
		return None

def add_info_from_pbp(rom: ROM, metadata: Metadata, pbp_file: bytes):
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
		parse_param_sfo(str(rom.path), metadata, param_sfo)
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

def add_psp_system_info(metadata: Metadata):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.analog_sticks = 1
	builtin_gamepad.face_buttons = 4 #also Start, Select
	builtin_gamepad.shoulder_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)

def get_image_from_iso(iso: 'PyCdlib', path: str) -> 'Image':
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
	return None

def add_psp_metadata(game: ROMGame):
	add_psp_system_info(game.metadata)

	if game.rom.extension == 'pbp':
		game.metadata.categories = game.metadata.categories[:-1]
		add_info_from_pbp(game.rom, game.metadata, cast(FileROM, game.rom).read())
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
				#This would be more like a build date (seems to be the same across all files) rather than the release date
				year = date.years_since_1900 + 1900
				month = date.month
				day = date.day_of_month
				game.metadata.specific_info['Build-Date'] = Date(year, month, day)
				guessed = Date(year, month, day, True)
				if guessed.is_better_than(game.metadata.release_date):
					game.metadata.release_date = guessed
				parse_param_sfo(str(game.rom.path), game.metadata, param_sfo_buf.getvalue())
			except PyCdlibInvalidInput:
				try:
					iso.get_record(iso_path='/UMD_VIDEO/PARAM.SFO')
					#We could parse this PARAM.SFO but there's not much point given we aren't going to make a launcher for UMD videos at this stage
					#TODO There is also potentially /UMD_AUDIO/ I think too so I should rewrite this one day
					game.metadata.specific_info['PlayStation-Category'] = 'UMD Video'
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
		parse_product_code(game.metadata, game.metadata.product_code)
