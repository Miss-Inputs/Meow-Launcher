import logging
import os
import statistics
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional, cast
from xml.etree import ElementTree

from meowlauncher.config.platform_config import platform_configs
from meowlauncher.games.common.engine_detect import \
    try_and_detect_engine_from_folder
from meowlauncher.games.roms.rom import ROM, FolderROM
from meowlauncher.metadata import Date
from meowlauncher.util.utils import load_dict

from .common.gametdb import TDB, add_info_from_tdb
from .common.nintendo_common import (WiiU3DSRegionCode,
                                     add_info_from_local_titles)

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

logger = logging.getLogger(__name__)
_nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')

_languages = {
	'ja': 'Japanese',
	'en': 'English',
	'fr': 'French',
	'de': 'German',
	'it': 'Italian',
	'es': 'Spanish',
	'zhs': 'Chinese (Simplified)',
	'ko': 'Korean',
	'nl': 'Dutch',
	'pt': 'Portuguese',
	'ru': 'Russian',
	'zht': 'Chinese (Traditional)',
}

class WiiUVirtualConsolePlatform(Enum):
	DS = 'D'
	NES = 'F'
	SNES = 'J'
	N64 = 'N'
	GBAOrPCEngine = 'P' #interesting…
	Wii = 'V' #Not really virtual console but eh
	MSX = 'M'
	#Is there a Game Boy one (for the Kirby's Dream Land inside SSB4, if that works that way?)

	#Just putting these here in the enum so I can properly use them
	GBA = 'GBA'
	PCEngine = 'PCEngine'

def _load_tdb() -> Optional[TDB]:
	if not 'Wii U' in platform_configs:
		return None
	tdb_path = platform_configs['Wii U'].options.get('tdb_path')
	if not tdb_path:
		return None

	try:
		return TDB(ElementTree.parse(tdb_path))
	except (ElementTree.ParseError, OSError):
		logger.exception('Oh no failed to load Wii U TDB because')
		return None
_tdb = _load_tdb()

def _add_cover(metadata: 'Metadata', product_code: str, licensee_code: str) -> None:
	#Intended for the covers database from GameTDB
	covers_path = platform_configs['Wii U'].options.get('covers_path')
	if not covers_path:
		return
	cover_base_path = covers_path.joinpath(product_code)
	other_cover_base_path = covers_path.joinpath(licensee_code + product_code)
	for ext in ('png', 'jpg'):
		cover_path = cover_base_path.with_suffix(os.extsep + ext)
		if cover_path.is_file():
			metadata.images['Cover'] = cover_path
			break
		other_cover_path = other_cover_base_path.with_suffix(os.extsep + ext)
		if other_cover_path.is_file():
			metadata.images['Cover'] = other_cover_path
			break

def _add_meta_xml_metadata(metadata: 'Metadata', meta_xml: ElementTree.ElementTree) -> None:
	#version = 33 for digital stuff, sometimes 32 otherwise?, content_platform = WUP, ext_dev_urcc = some kiosk related thingo
	#logo_type = 2 on third party stuff?, app_launch_type = 1 on parental controls/H&S/Wii U Chat and 0 on everything else?, invisible_flag = maybe just for keeping stuff out of the daily log?, no_managed_flag, no_event_log, no_icon_database, launching_flag, install_flag, closing_msg, group_id, boss_id, os_version, app_size, common_boss_size, account_boss_size, save_no_rollback, join_game_id, join_game_mode_mask, bg_daemon_enable, olv_accesskey, wood_tin, e_manual = I guess it's 1 if it has a manual, e_manual_version, eula_version, direct_boot, reserved_flag{0-7}, add_on_unique_id{0-31} = DLC probs?
	product_code = meta_xml.findtext('product_code')
	if product_code:
		metadata.product_code = product_code
		try:
			metadata.specific_info['Virtual Console Platform'] = WiiUVirtualConsolePlatform(metadata.product_code[6])
		except ValueError:
			pass
		gametdb_id = product_code[-4:]
		add_info_from_tdb(_tdb, metadata, gametdb_id)

	company_code = meta_xml.findtext('company_code')
	if company_code:
		if company_code in _nintendo_licensee_codes:
			metadata.publisher = _nintendo_licensee_codes[company_code]
		elif len(company_code) == 4 and company_code.startswith('00'):
			if company_code[2:] in _nintendo_licensee_codes:
				metadata.publisher = _nintendo_licensee_codes[company_code[2:]]

	if product_code and company_code:
		_add_cover(metadata, product_code[-4:], company_code[2:])

	mastering_date_text = meta_xml.findtext('mastering_date')
	#Usually blank? Sometimes exists though
	if mastering_date_text:
		try:
			mastering_datetime = datetime.fromisoformat(mastering_date_text[:10])
			mastering_date = Date(mastering_datetime.year, mastering_datetime.month, mastering_datetime.day)
			metadata.specific_info['Mastering Date'] = mastering_date
			guessed_date = Date(mastering_date.year, mastering_date.month, mastering_date.day, True)
			if guessed_date.is_better_than(metadata.release_date):
				metadata.release_date = guessed_date
		except ValueError:
			logger.debug('%s mastering date is wack %s', product_code, mastering_date_text)
	#Maybe we can use these to figure out if it creates a save file or not…
	metadata.specific_info['Common Save Size'] = int(meta_xml.findtext('common_save_size') or '0', 16)
	metadata.specific_info['Account Save Size'] = int(meta_xml.findtext('account_save_size') or '0', 16)

	metadata.specific_info['Title ID'] = meta_xml.findtext('title_id')
	version = meta_xml.findtext('title_version')
	if version:
		metadata.specific_info['Version'] = 'v' + version

	region = meta_xml.findtext('region')
	region_codes = set()
	if region:
		try:
			region_flags = int(region, 16)
			for region_code in WiiU3DSRegionCode:
				if region_code in (WiiU3DSRegionCode.RegionFree, WiiU3DSRegionCode.WiiURegionFree):
					continue
				if region_code.value & region_flags:
					region_codes.add(region_code)
			metadata.specific_info['Region Code'] = region_codes
		except ValueError:
			metadata.specific_info['Region Code'] = '0x' + region

	#Tempted to reuse wii.parse_ratings, but I might not because it's just a bit different
	rating_tags = {tag: int(tag.text) for tag in meta_xml.iter() if tag.tag.startswith('pc_') and tag.text}
	ratings = {tag.tag: rating & 0b0001_1111 for tag, rating in rating_tags.items() if (rating & 0b1000_0000) == 0 and (rating & 0b0100_0000) == 0}
	if ratings:
		try:
			rating = statistics.mode(ratings.values())
		except statistics.StatisticsError:
			rating = max(ratings.values())
		metadata.specific_info['Age Rating'] = rating
		if 'pc_cero' in ratings:
			metadata.specific_info['CERO Rating'] = ratings['pc_cero']
		if 'pc_esrb' in ratings:
			metadata.specific_info['ESRB Rating'] = ratings['pc_esrb']
		if 'pc_usk' in ratings:
			metadata.specific_info['USK Rating'] = ratings['pc_usk']
		if 'pc_pegi_gen' in ratings:
			metadata.specific_info['PEGI Rating'] = ratings['pc_pegi_gen']
		#There are more but that will do

	# #These may not be accurate at all?
	# metadata.specific_info['Uses-Nunchuk'] = meta_xml.findtext('ext_dev_nunchaku') != '0'
	# metadata.specific_info['Uses-Classic-Controller'] = meta_xml.findtext('ext_dev_classic') != '0'
	# metadata.specific_info['Uses-Balance-Board'] = meta_xml.findtext('ext_dev_board') != '0' #maybe?
	# metadata.specific_info['Uses-USB-Keyboard'] = meta_xml.findtext('ext_dev_usb_keyboard') != '0'
	# uses_etc = meta_xml.findtext('ext_dev_etc') != '0' #???
	# if uses_etc:
	# 	metadata.specific_info['Uses-Etc'] = meta_xml.findtext('ext_dev_etc_name')

	#drc = meta_xml.findtext('drc_use') != '0'
	#network = meta_xml.findtext('network_use') != '0'
	#online_account = meta_xml.findtext('online_account_use') != '0'
	
	short_names = {}
	long_names = {}
	publishers = {}
	for lang_code, lang_name in _languages.items():
		short_name = meta_xml.findtext('shortname_' + lang_code)
		if short_name:
			short_names[lang_name] = short_name
		long_name = meta_xml.findtext('longname_' + lang_code)
		if long_name:
			long_names[lang_name] = long_name.replace('\n', ': ') #Newlines seem to be used here to separate subtitles
		publisher = meta_xml.findtext('publisher_' + lang_code)
		if publisher:
			publishers[lang_name] = publisher

	add_info_from_local_titles(metadata, short_names, long_names, publishers, region_codes)

def _add_homebrew_meta_xml_metadata(rom: ROM, metadata: 'Metadata', meta_xml: ElementTree.ElementTree) -> None:
	name = meta_xml.findtext('name')
	if name:
		rom.ignore_name = True
		metadata.add_alternate_name(name, 'Banner Title')
	metadata.developer = metadata.publisher = meta_xml.findtext('coder')
	metadata.specific_info['Version'] = meta_xml.findtext('version')
	url = meta_xml.findtext('url')
	if url:
		metadata.documents['Homepage'] = url
	release_date_text = meta_xml.findtext('release_date')
	if release_date_text:
		metadata.release_date = Date(release_date_text[0:4], release_date_text[4:6], release_date_text[6:8])

	short_description = meta_xml.findtext('short_description')
	if short_description:
		metadata.descriptions['Short Description'] = short_description
	long_description = meta_xml.findtext('long_description')
	if long_description:
		metadata.descriptions['Long Description'] = long_description
	metadata.specific_info['Homebrew Category'] = meta_xml.findtext('category') or 'None' #Makes me wonder if it's feasible to include an option to get categories not from folders…

def _add_rpx_metadata(rom: ROM, metadata: 'Metadata') -> None:
	#The .rpx itself is not interesting and basically just a spicy ELF
	#This is going to assume we are looking at a homebrew folder

	try:
		#info.json has the same info? But it's not always there
		_add_homebrew_meta_xml_metadata(rom, metadata, ElementTree.parse(rom.path.with_name('meta.xml')))
		if metadata.categories[-1] == rom.path.parent.name:
			metadata.categories = metadata.categories[:-1]
	except ElementTree.ParseError:
		logging.warning('Some parse error happened for %s', rom, exc_info=True)
	except FileNotFoundError:
		pass
	homebrew_banner_path = rom.path.with_name('icon.png')
	if homebrew_banner_path.is_file():
		metadata.images['Banner'] = homebrew_banner_path

def add_folder_metadata(rom: FolderROM, metadata: 'Metadata') -> None:
	content_dir = rom.get_subfolder('content')
	meta_dir = rom.get_subfolder('meta')
	assert content_dir and meta_dir, 'It should be impossible for content_dir or meta_dir to be none, otherwise this would not have even been detected as a folder'
	
	metadata.specific_info['Executable Name'] = rom.relevant_files['rpx'].name

	#TODO: Move this over to engine_detect
	if rom.path.joinpath('code', 'UnityEngine_dll.rpl').is_file():
		#Unity games on Wii U just have a "Data" folder under content with no executable (because it's over here in code), so our usual detection won't work; not sure about other cross platform engines
		metadata.specific_info['Engine'] = 'Unity'
	if content_dir.joinpath('assets').is_dir() and all(content_dir.joinpath('app', file).is_dir() for file in ('appinfo.xml', 'config.xml', 'index.html')):
		metadata.specific_info['Engine'] = 'Nintendo Web Framework'
	
	engine = try_and_detect_engine_from_folder(content_dir, metadata)
	if engine:
		metadata.specific_info['Engine'] = engine

	#Seemingly this can actually sometimes be all lowercase? I should make this check case insensitive but I don't really care too much
	icon_path = meta_dir.joinpath('iconTex.tga')
	if icon_path.is_file():
		metadata.images['Icon'] = icon_path
	boot_drc_path = meta_dir.joinpath('bootDrcTex.tga') #Image displayed on the gamepad while loading
	if boot_drc_path.is_file():
		metadata.images['Gamepad Boot Image'] = boot_drc_path
	boot_tv_path = meta_dir.joinpath('bootTvTex.tga') #Generally just bootDrcTex but higher resolution (and for the TV)
	if boot_tv_path.is_file():
		metadata.images['TV Boot Image'] = boot_tv_path
	boot_logo_path = meta_dir.joinpath('bootLogoTex.tga')
	if boot_logo_path.is_file():
		metadata.images['Boot Logo'] = boot_logo_path
	#There is also a Manual.bfma in here, bootMovie.h264 and bootSound.btsnd, and some ratings images like "CERO_ja.jpg" and "PEGI_en.jpg" except they're 1 byte so I dunno

	meta_xml_path = meta_dir.joinpath('meta.xml')
	try:
		meta_xml = ElementTree.parse(meta_xml_path)
		_add_meta_xml_metadata(metadata, meta_xml)
	except FileNotFoundError:
		pass

	if metadata.specific_info.get('Virtual Console Platform') == WiiUVirtualConsolePlatform.GBAOrPCEngine:
		metadata.specific_info['Virtual Console Platform'] = WiiUVirtualConsolePlatform.GBA if rom.name == 'm2engage' else WiiUVirtualConsolePlatform.PCEngine

def add_wii_u_custom_info(game: 'ROMGame') -> None:
	if game.rom.is_folder:
		add_folder_metadata(cast(FolderROM, game.rom), game.metadata)
	if game.rom.extension == 'rpx':
		_add_rpx_metadata(game.rom, game.metadata)
	#We could leverage Cemu to get the meta.xml out of discs with -e <disc.wud> -p meta/meta.xml but that 1) sounds annoying to go back into emulator_config to get the path of Cemu and such and that might inevitably cause a recursive import 2) pops up a dialog box if the key for the wud isn't there or fails in some other way
