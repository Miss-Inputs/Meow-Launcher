import io
import logging
from pathlib import Path
import struct  # To handle struct.error
from typing import TYPE_CHECKING, Any, Optional, cast

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

try:

	from pycdlib import PyCdlib
	from pycdlib.pycdlibexception import PyCdlibInvalidInput, PyCdlibInvalidISO
	have_pycdlib = True
except ModuleNotFoundError:
	have_pycdlib = False

from meowlauncher.games.roms.rom import FileROM, FolderROM
from meowlauncher.metadata import Date

from .common.playstation_common import parse_param_sfo, parse_product_code
from .static_platform_info import add_psp_info

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

logger = logging.getLogger(__name__)

def load_image_from_bytes(data: bytes) -> Optional['Image.Image']:
	bitmap_data_io = io.BytesIO(data)
	try:
		image = Image.open(bitmap_data_io)
		return image
	except OSError:
		return None

def add_info_from_pbp(rompath_just_for_warning: str, metadata: 'Metadata', pbp_file: bytes) -> None:
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
		parse_param_sfo(rompath_just_for_warning, metadata, param_sfo)
	if have_pillow:
		if icon0_offset > param_sfo_offset:
			banner = load_image_from_bytes(pbp_file[icon0_offset:icon1_offset])
			if banner:
				metadata.images['Banner'] = banner
		if icon1_offset > icon0_offset:
			#Dunno what these 3 other images do exactly, so they have crap names for now
			icon1 = load_image_from_bytes(pbp_file[icon1_offset:pic0_offset])
			if icon1:
				metadata.images['Icon 1'] = icon1
		if pic0_offset > icon1_offset:
			pic0 = load_image_from_bytes(pbp_file[pic0_offset:pic1_offset])
			if pic0:
				metadata.images['Picture 0'] = pic0
		if pic1_offset > pic0_offset:
			pic1 = load_image_from_bytes(pbp_file[pic1_offset:snd0_offset])
			if pic1:
				metadata.images['Background Image'] = pic1

def get_image_from_iso(iso: 'PyCdlib', path: Path, object_for_warning: Any=None) -> 'Image':
	try:
		with iso.open_file_from_iso(iso_path=str(path)) as image_data:
			try:
				image = Image.open(image_data)
				image.load() #Force Pillow to figure out if the image is valid or not, and also copy the image data
				return image
			except (OSError, SyntaxError):
				logging.exception('Error getting image %s inside ISO %s', path, object_for_warning or iso)
				return None
	except PyCdlibInvalidInput:
		#It is okay for a disc to be missing something
		pass
	return None

def add_psp_iso_info(path: Path, metadata: 'Metadata') -> None:
	iso = PyCdlib()
	try:
		iso.open(str(path))
		try:
			with iso.open_file_from_iso(iso_path='/PSP_GAME/PARAM.SFO') as param_sfo:
				parse_param_sfo(path, metadata, param_sfo.read())

			date = iso.get_record(iso_path='/PSP_GAME/PARAM.SFO').date
			#This would be more like a build date (seems to be the same across all files) rather than the release date
			year = date.years_since_1900 + 1900
			month = date.month
			day = date.day_of_month
			metadata.specific_info['Build Date'] = Date(year, month, day)
			guessed = Date(year, month, day, True)
			if guessed.is_better_than(metadata.release_date):
				metadata.release_date = guessed
		except PyCdlibInvalidInput:
			try:
				iso.get_record(iso_path='/UMD_VIDEO/PARAM.SFO')
				#We could parse this PARAM.SFO but there's not much point given we aren't going to make a launcher for UMD videos at this stage
				#TODO There is also potentially /UMD_AUDIO/ I think too so I should rewrite this one day
				metadata.specific_info['PlayStation Category'] = 'UMD Video'
				return
			except PyCdlibInvalidInput:
				logger.info('%s has no PARAM.SFO inside', path)
		else:
			if have_pillow:
				metadata.images['Banner'] = get_image_from_iso(iso, '/PSP_GAME/ICON0.PNG', path)
				metadata.images['Icon 1'] = get_image_from_iso(iso, '/PSP_GAME/ICON1.PNG', path)
				metadata.images['Picture 0'] = get_image_from_iso(iso, '/PSP_GAME/PIC0.PNG', path)
				metadata.images['Background Image'] = get_image_from_iso(iso, '/PSP_GAME/PIC1.PNG', path)
		finally:
			iso.close()	
	except PyCdlibInvalidISO:
		logger.info('%s is invalid ISO and has some struct.error', path, exc_info=True)
	except struct.error:
		logger.info('%s is invalid ISO and has some struct.error', path, exc_info=True)
		
def add_psp_custom_info(game: 'ROMGame') -> None:
	add_psp_info(game.metadata)

	if game.rom.is_folder:
		pbp = cast(FolderROM, game.rom).relevant_files['pbp']
		game.metadata.specific_info['Executable Name'] = pbp.name #Probably just EBOOT.PBP but you never know eh
		add_info_from_pbp(str(game.rom), game.metadata, pbp.read_bytes())
	elif game.rom.extension == 'pbp':
		#Unlikely to happen now that we have a folder check
		game.metadata.categories = game.metadata.categories[:-1]
		add_info_from_pbp(str(game.rom), game.metadata, cast(FileROM, game.rom).read())
		#These are basically always named EBOOT.PBP (due to how PSPs work I guess), so that's not a very good launcher name, and use the folder it's stored in instead
		if game.rom.name.lower() == 'eboot':
			game.metadata.add_alternate_name(game.rom.path.parent.name, 'Folder Name')
			game.rom.ignore_name = True
	elif game.rom.extension == 'iso' and have_pycdlib:
		add_psp_iso_info(game.rom.path, game.metadata)

	#https://www.psdevwiki.com/ps3/Productcode#Physical
	if game.metadata.product_code:
		parse_product_code(game.metadata, game.metadata.product_code)
