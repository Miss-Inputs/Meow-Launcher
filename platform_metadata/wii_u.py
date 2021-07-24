import os
import statistics
from datetime import datetime
from enum import Enum
from xml.etree import ElementTree

from common import load_dict
from config.main_config import main_config
from config.system_config import system_configs
from metadata import Date
from pc_common_metadata import try_and_detect_engine_from_folder

from ._3ds import \
    _3DSRegionCode  # I should move this to some common module, maybe
from .gametdb import TDB, add_info_from_tdb

nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')

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

def load_tdb():
	if not 'Wii U' in system_configs:
		return None
	tdb_path = system_configs['Wii U'].options.get('tdb_path')
	if not tdb_path:
		return None

	try:
		return TDB(ElementTree.parse(tdb_path))
	except (ElementTree.ParseError, OSError) as blorp:
		if main_config.debug:
			print('Oh no failed to load Wii U TDB because', blorp)
		return None
tdb = load_tdb()

def add_cover(metadata, product_code, licensee_code):
	#Intended for the covers database from GameTDB
	covers_path = system_configs['Wii U'].options.get('covers_path')
	if not covers_path:
		return
	cover_path = os.path.join(covers_path, product_code)
	other_cover_path = os.path.join(covers_path + licensee_code, product_code)
	for ext in ('png', 'jpg'):
		if os.path.isfile(cover_path + os.extsep + ext):
			metadata.images['Cover'] = cover_path + os.extsep + ext
			break
		if os.path.isfile(other_cover_path + os.extsep + ext):
			metadata.images['Cover'] = other_cover_path + os.extsep + ext
			break

def add_meta_xml_metadata(metadata, meta_xml):
	#version = 33 for digital stuff, sometimes 32 otherwise?, content_platform = WUP, ext_dev_urcc = some kiosk related thingo
	#logo_type = 2 on third party stuff?, app_launch_type = 1 on parental controls/H&S/Wii U Chat and 0 on everything else?, invisible_flag = maybe just for keeping stuff out of the daily log?, no_managed_flag, no_event_log, no_icon_database, launching_flag, install_flag, closing_msg, group_id, boss_id, os_version, app_size, common_boss_size, account_boss_size, save_no_rollback, join_game_id, join_game_mode_mask, bg_daemon_enable, olv_accesskey, wood_tin, e_manual = I guess it's 1 if it has a manual, e_manual_version, eula_version, direct_boot, reserved_flag{0-7}, add_on_unique_id{0-31} = DLC probs?
	product_code = meta_xml.findtext('product_code')
	metadata.product_code = product_code
	try:
		metadata.specific_info['Virtual-Console-Platform'] = WiiUVirtualConsolePlatform(metadata.product_code[6])
	except ValueError:
		pass
	gametdb_id = product_code[-4:]
	add_info_from_tdb(tdb, metadata, gametdb_id)

	company_code = meta_xml.findtext('company_code')
	if company_code in nintendo_licensee_codes:
		metadata.publisher = nintendo_licensee_codes[company_code]
	elif len(company_code) == 4 and company_code.startswith('00'):
		if company_code[2:] in nintendo_licensee_codes:
			metadata.publisher = nintendo_licensee_codes[company_code[2:]]
		
	add_cover(metadata, product_code[-4:], company_code[2:])

	mastering_date_text = meta_xml.findtext('mastering_date')
	#Usually blank? Sometimes exists though
	if mastering_date_text:
		try:
			mastering_datetime = datetime.fromisoformat(mastering_date_text[:10])
			mastering_date = Date(mastering_datetime.year, mastering_datetime.month, mastering_datetime.day)
			metadata.specific_info['Mastering-Date'] = mastering_date
			guessed_date = Date(mastering_date.year, mastering_date.month, mastering_date.day, True)
			if guessed_date.is_better_than(metadata.release_date):
				metadata.release_date = guessed_date
		except ValueError:
			#print(mastering_date_text)
			pass
	#Maybe we can use these to figure out if it creates a save file or not…
	metadata.specific_info['Common-Save-Size'] = int(meta_xml.findtext('common_save_size'), 16)
	metadata.specific_info['Account-Save-Size'] = int(meta_xml.findtext('account_save_size'), 16)

	metadata.specific_info['Title-ID'] = meta_xml.findtext('title_id')
	version = meta_xml.findtext('title_version')
	if version:
		metadata.specific_info['Version'] = 'v' + version

	region = meta_xml.findtext('region')
	region_codes = []
	if region:
		try:
			region_flags = int(region, 16)
			for region in _3DSRegionCode:
				if region in (_3DSRegionCode.RegionFree, _3DSRegionCode.WiiURegionFree):
					continue
				if region.value & region_flags:
					region_codes.append(region)
			metadata.specific_info['Region-Code'] = region_codes
		except ValueError:
			metadata.specific_info['Region-Code'] = '0x' + region

	#Tempted to reuse wii.parse_ratings, but I might not because it's just a bit different
	rating_tags = {tag: int(tag.text) for tag in meta_xml.iter() if tag.tag.startswith('pc_')}
	ratings = {tag.tag: rating & 0b0001_1111 for tag, rating in rating_tags.items() if (rating & 0b1000_0000) == 0 and (rating & 0b0100_0000) == 0}
	if ratings:
		try:
			rating = statistics.mode(ratings.values())
		except statistics.StatisticsError:
			rating = max(ratings.values())
		metadata.specific_info['Age-Rating'] = rating
		if 'pc_cero' in ratings:
			metadata.specific_info['CERO-Rating'] = ratings['pc_cero']
		if 'pc_esrb' in ratings:
			metadata.specific_info['ESRB-Rating'] = ratings['pc_esrb']
		if 'pc_usk' in ratings:
			metadata.specific_info['USK-Rating'] = ratings['pc_usk']
		if 'pc_pegi_gen' in ratings:
			metadata.specific_info['PEGI-Rating'] = ratings['pc_pegi_gen']
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

	languages = {
		'ja': 'Japanese',
		'en': 'English',
		'fr': 'French',
		'de': 'German',
		'it': 'Italian',
		'es': 'Spanish',
		'zhs': 'Simplified Chinese',
		'ko': 'Korean',
		'nl': 'Dutch',
		'pt': 'Portugese',
		'ru': 'Russian',
		'zht': 'Traditional Chinese',
	}
	
	short_names = {}
	long_names = {}
	publishers = {}
	for lang_code, lang_name in languages.items():
		short_name = meta_xml.findtext('shortname_' + lang_code)
		if short_name:
			short_names[lang_name] = short_name
		long_name = meta_xml.findtext('longname_' + lang_code)
		if long_name:
			long_names[lang_name] = long_name.replace('\n', ': ') #Newlines seem to be used here to separate subtitles
		publisher = meta_xml.findtext('publisher_' + lang_code)
		if publisher:
			publishers[lang_name] = publisher

	#Just straight up copypaste from _3ds.py fuck it
	local_short_title = None
	local_long_title = None
	local_publisher = None
	if _3DSRegionCode.RegionFree in region_codes or _3DSRegionCode.USA in region_codes or _3DSRegionCode.Europe in region_codes:
		#We shouldn't assume that Europe is English-speaking but we're going to
		local_short_title = short_names.get('English')
		local_long_title = long_names.get('English')
		local_publisher = publishers.get('English')
	elif _3DSRegionCode.Japan in region_codes:
		local_short_title = short_names.get('Japanese')
		local_long_title = long_names.get('Japanese')
		local_publisher = publishers.get('Japanese')
	elif _3DSRegionCode.China in region_codes:
		local_short_title = short_names.get('Simplified Chinese')
		local_long_title = long_names.get('Simplified Chinese')
		local_publisher = publishers.get('Simplified Chinese')
	elif _3DSRegionCode.Korea in region_codes:
		local_short_title = short_names.get('Korean')
		local_long_title = long_names.get('Korean')
		local_publisher = publishers.get('Korean')
	elif _3DSRegionCode.Taiwan in region_codes:
		local_short_title = short_names.get('Traditional Chinese')
		local_long_title = long_names.get('Traditional Chinese')
		local_publisher = publishers.get('Traditional Chinese')
	else: #If none of that is in the region code? Unlikely but I dunno maybe
		if short_names:
			local_short_title = list(short_names.values())[0]
		if long_names:
			local_long_title = list(long_names.values())[0]
		if publishers:
			local_publisher = list(publishers.values())[0]

	if local_short_title:
		metadata.add_alternate_name(local_short_title, 'Short-Title')
	if local_long_title:
		metadata.add_alternate_name(local_long_title, 'Title')
	if local_publisher and not metadata.publisher:
		metadata.publisher = local_publisher

	for lang, short_title in short_names.items():
		if short_title != local_short_title:
			metadata.add_alternate_name(short_title, '{0}-Short-Title'.format(lang.replace(' ', '-')))
	for lang, long_title in long_names.items():
		if long_title != local_long_title:
			metadata.add_alternate_name(long_title, '{0}-Title'.format(lang.replace(' ', '-')))
	for lang, publisher in publishers.items():
		if publisher not in (metadata.publisher, local_publisher):
			metadata.specific_info['{0}-Publisher'.format(lang.replace(' ', '-'))] = publisher

def add_homebrew_meta_xml_metadata(rom, metadata, meta_xml):
	name = meta_xml.findtext('name')
	if name:
		rom.ignore_name = True
		metadata.add_alternate_name(name, 'Banner-Title')
	metadata.developer = metadata.publisher = meta_xml.findtext('coder')
	metadata.specific_info['Version'] = meta_xml.findtext('version')
	metadata.documents['Homepage'] = meta_xml.findtext('url')
	release_date_text = meta_xml.findtext('release_date')
	if release_date_text:
		metadata.release_date = Date(release_date_text[0:4], release_date_text[4:6], release_date_text[6:8])

	metadata.descriptions['Short-Description'] = meta_xml.findtext('short_description')
	metadata.descriptions['Long-Description'] = meta_xml.findtext('long_description')
	metadata.specific_info['Homebrew-Category'] = meta_xml.findtext('category') #Makes me wonder if it's feasible to include an option to get categories not from folders…

def add_rpx_metadata(rom, metadata):
	#The .rpx itself is not interesting and basically just a spicy ELF
	#This is going to assume we are looking at a homebrew folder

	parent_folder = os.path.dirname(rom.path)

	try:
		#info.json has the same info? But it's not always there
		add_homebrew_meta_xml_metadata(rom, metadata, ElementTree.parse(os.path.join(parent_folder, 'meta.xml')))
		if metadata.categories[-1] == os.path.basename(parent_folder):
			metadata.categories = metadata.categories[:-1]
	except FileNotFoundError:
		pass
	homebrew_banner_path = os.path.join(parent_folder, 'icon.png')
	if os.path.isfile(homebrew_banner_path):
		metadata.images['Banner'] = homebrew_banner_path

def add_folder_metadata(rom, metadata):
	content_dir = rom.get_subfolder('content')
	meta_dir = rom.get_subfolder('meta')
	
	metadata.specific_info['Executable-Name'] = os.path.basename(rom.relevant_files['rpx'])

	#While we are here… using pc_common_metadata engine detect on the content folder almost seems like a good idea too, but it won't accomplish much so far
	if os.path.isfile(os.path.join(rom.path, 'code', 'UnityEngine_dll.rpl')):
		#Unity games on Wii U just have a "Data" folder under content with no executable (because it's over here in code), so our usual detection won't work; not sure about other cross platform engines
		metadata.specific_info['Engine'] = 'Unity'
	if os.path.isdir(os.path.join(content_dir, 'assets')) and all(os.path.isfile(os.path.join(content_dir, 'app', file)) for file in ('appinfo.xml', 'config.xml', 'index.html')):
		metadata.specific_info['Engine'] = 'Nintendo Web Framework'
	
	engine = try_and_detect_engine_from_folder(content_dir, metadata)
	if engine:
		metadata.specific_info['Engine'] = engine

	#Seemingly this can actually sometimes be all lowercase? I should make this check case insensitive but I don't really care too much
	icon_path = os.path.join(meta_dir, 'iconTex.tga')
	if os.path.isfile(icon_path):
		metadata.images['Icon'] = icon_path
	boot_drc_path = os.path.join(meta_dir, 'bootDrcTex.tga') #Image displayed on the gamepad while loading
	if boot_drc_path:
		metadata.images['Gamepad-Boot-Image'] = boot_drc_path
	boot_tv_path = os.path.join(meta_dir, 'bootTvTex.tga') #Generally just bootDrcTex but higher resolution (and for the TV)
	if boot_tv_path:
		metadata.images['TV-Boot-Image'] = boot_tv_path
	boot_logo_path = os.path.join(meta_dir, 'bootLogoTex.tga')
	if boot_logo_path:
		metadata.images['Boot-Logo'] = boot_logo_path
	#There is also a Manual.bfma in here, bootMovie.h264 and bootSound.btsnd, and some ratings images like "CERO_ja.jpg" and "PEGI_en.jpg" except they're 1 byte so I dunno

	meta_xml_path = os.path.join(meta_dir, 'meta.xml')
	try:
		meta_xml = ElementTree.parse(meta_xml_path)
		add_meta_xml_metadata(metadata, meta_xml)
	except FileNotFoundError:
		pass

	if metadata.specific_info.get('Virtual-Console-Platform') == WiiUVirtualConsolePlatform.GBAOrPCEngine:
		metadata.specific_info['Virtual-Console-Platform'] = WiiUVirtualConsolePlatform.GBA if rom.name == 'm2engage' else WiiUVirtualConsolePlatform.PCEngine

def add_wii_u_metadata(game):
	if game.rom.is_folder:
		add_folder_metadata(game.rom, game.metadata)
	if game.rom.extension == 'rpx':
		add_rpx_metadata(game.rom, game.metadata)
	#We could leverage Cemu to get the meta.xml out of discs with -e <disc.wud> -p meta/meta.xml but that 1) sounds annoying to go back into emulator_config to get the path of Cemu and such and that might inevitably cause a recursive import 2) pops up a dialog box if the key for the wud isn't there or fails in some other way
