import io
import logging
from pathlib import Path
import struct  # To handle struct.error
from typing import TYPE_CHECKING, Any, cast

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

try:

	from pycdlib import PyCdlib
	from pycdlib.dr import DirectoryRecord
	from pycdlib.pycdlibexception import PyCdlibInvalidInput, PyCdlibInvalidISO
	have_pycdlib = True
except ModuleNotFoundError:
	have_pycdlib = False

from meowlauncher.games.roms.rom import FileROM, FolderROM
from meowlauncher.info import Date

from .common.playstation_common import parse_param_sfo, parse_product_code
from .static_platform_info import add_psp_info

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.info import GameInfo

logger = logging.getLogger(__name__)

def _load_image_from_bytes(data: bytes) -> 'Image.Image | None':
	bitmap_data_io = io.BytesIO(data)
	try:
		image = Image.open(bitmap_data_io)
	except OSError:
		return None
	else:
		return image

def _add_info_from_pbp(rompath_just_for_warning: Any, game_info: 'GameInfo', pbp_file: bytes) -> None:
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
		parse_param_sfo(rompath_just_for_warning, game_info, param_sfo)
	if have_pillow:
		if icon0_offset > param_sfo_offset:
			banner = _load_image_from_bytes(pbp_file[icon0_offset:icon1_offset])
			if banner:
				game_info.images['Banner'] = banner
		if icon1_offset > icon0_offset:
			#Dunno what these 3 other images do exactly, so they have crap names for now
			icon1 = _load_image_from_bytes(pbp_file[icon1_offset:pic0_offset])
			if icon1:
				game_info.images['Icon 1'] = icon1
		if pic0_offset > icon1_offset:
			pic0 = _load_image_from_bytes(pbp_file[pic0_offset:pic1_offset])
			if pic0:
				game_info.images['Picture 0'] = pic0
		if pic1_offset > pic0_offset:
			pic1 = _load_image_from_bytes(pbp_file[pic1_offset:snd0_offset])
			if pic1:
				game_info.images['Background Image'] = pic1

def _get_image_from_iso(iso: 'PyCdlib', inner_path: str, object_for_warning: Any=None) -> 'Image.Image | None':
	try:
		with iso.open_file_from_iso(iso_path=inner_path) as image_data:
			try:
				image = Image.open(image_data)
				image.load() #Force Pillow to figure out if the image is valid or not, and also copy the image data
			except (OSError, SyntaxError):
				logger.info('Error getting image %s inside ISO %s', inner_path, object_for_warning or iso)
				return None
			else:
				return image
	except PyCdlibInvalidInput:
		#It is okay for a disc to be missing something
		pass
	return None

def _add_psp_iso_info(path: Path, game_info: 'GameInfo') -> None:
	with path.open('rb') as iso_file:
		try:
			iso = PyCdlib()
			iso.open_fp(iso_file)
			try:
				with iso.open_file_from_iso(iso_path='/PSP_GAME/PARAM.SFO') as param_sfo:
					parse_param_sfo(path, game_info, param_sfo.read())

				date = cast(DirectoryRecord, iso.get_record(iso_path='/PSP_GAME/PARAM.SFO')).date
				#This would be more like a build date (seems to be the same across all files) rather than the release date
				year = date.years_since_1900 + 1900
				month = date.month
				day = date.day_of_month
				game_info.specific_info['Build Date'] = Date(year, month, day)
				guessed = Date(year, month, day, True)
				if guessed.is_better_than(game_info.release_date):
					game_info.release_date = guessed
			except PyCdlibInvalidInput:
				try:
					iso.get_record(iso_path='/UMD_VIDEO/PARAM.SFO')
					#We could parse this PARAM.SFO but there's not much point given we aren't going to make a launcher for UMD videos at this stage
					#TODO There is also potentially /UMD_AUDIO/ I think too so I should rewrite this one day
					game_info.specific_info['PlayStation Category'] = 'UMD Video'
					return
				except PyCdlibInvalidInput:
					logger.info('%s has no PARAM.SFO inside', path)
			else:
				if have_pillow:
					game_info.images.update(((k, v) for k, v in (
						('Banner', _get_image_from_iso(iso, '/PSP_GAME/ICON0.PNG', path)),
						('Icon 1', _get_image_from_iso(iso, '/PSP_GAME/ICON1.PNG', path)),
						('Picture 0', _get_image_from_iso(iso, '/PSP_GAME/PIC0.PNG', path)),
						('Background Image', _get_image_from_iso(iso, '/PSP_GAME/PIC1.PNG', path)),
					) if v
					))
		except PyCdlibInvalidISO:
			logger.info('%s is invalid ISO and has some struct.error', path, exc_info=True)
		except struct.error:
			logger.info('%s is invalid ISO and has some struct.error', path)
		
def add_psp_custom_info(game: 'ROMGame') -> None:
	"""Called from info_helpers for now"""
	add_psp_info(game.info)

	if game.rom.is_folder:
		pbp = cast(FolderROM, game.rom).relevant_files['pbp']
		game.info.specific_info['Executable Name'] = pbp.name #Probably just EBOOT.PBP but you never know eh
		_add_info_from_pbp(game.rom, game.info, pbp.read_bytes())
	elif game.rom.extension == 'pbp':
		#Unlikely to happen now that we have a folder check
		game.info.categories = game.info.categories[:-1]
		_add_info_from_pbp(game.rom, game.info, cast(FileROM, game.rom).read())
		#These are basically always named EBOOT.PBP (due to how PSPs work I guess), so that's not a very good launcher name, and use the folder it's stored in instead
		if game.rom.name.lower() == 'eboot':
			game.info.add_alternate_name(game.rom.path.parent.name, 'Folder Name')
			game.rom.ignore_name = True
	elif game.rom.extension == 'iso' and have_pycdlib:
		_add_psp_iso_info(game.rom.path, game.info)

	#https://www.psdevwiki.com/ps3/Productcode#Physical
	if game.info.product_code:
		parse_product_code(game.info, game.info.product_code)
