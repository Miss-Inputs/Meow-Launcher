import os
import statistics
from enum import Enum
from xml.etree import ElementTree

from config.main_config import main_config
from config.system_config import system_configs
from data.nintendo_licensee_codes import nintendo_licensee_codes
from metadata import Date

from ._3ds import \
    _3DSRegionCode  # I should move this to some common module, maybe
from .gametdb import TDB, add_info_from_tdb


class WiiUVirtualConsolePlatform(Enum):
	DS = 'D'
	NES = 'F'
	SNES = 'J'
	N64 = 'N'
	GBAOrPCEngine = 'P' #interesting…
	Wii = 'V' #Not really virtual console but eh
	#Is there a Game Boy one (for the Kirby's Dream Land inside SSB4, if that works that way?)

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

def add_meta_xml_metadata(metadata, meta_xml):
	#version = 33 for digital stuff, sometimes 32 otherwise?, content_platform = WUP, publisher_ja/en/etc, ext_dev_urcc = some kiosk related thingo
	#mastering_date = blank? (it is something like 2021-02-07 18:59:24 on discs), logo_type = 2 on third party stuff?, app_launch_type = 1 on parental controls/H&S/Wii U Chat and 0 on everything else?, invisible_flag = maybe just for keeping stuff out of the daily log?, no_managed_flag, no_event_log, no_icon_database, launching_flag, install_flag, closing_msg, title_version, title_id, group_id, boss_id, os_version, app_size, common_boss_size, account_boss_size, save_no_rollback, join_game_id, join_game_mode_mask, bg_daemon_enable, olv_accesskey, wood_tin, e_manual = I guess it's 1 if it has a manual, e_manual_version, eula_version, direct_boot, reserved_flag{0-7}, add_on_unique_id{0-31} = DLC probs?
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

	#Maybe we can use these to figure out if it creates a save file or not…
	metadata.specific_info['Common-Save-Size'] = int(meta_xml.findtext('common_save_size'), 16)
	metadata.specific_info['Account-Save-Size'] = int(meta_xml.findtext('account_save_size'), 16)

	region = meta_xml.findtext('region')
	if region:
		try:
			region_flags = int(region, 16)
			region_codes = []
			for region in _3DSRegionCode:
				if region in (_3DSRegionCode.RegionFree, _3DSRegionCode.WiiURegionFree):
					continue
				if region.value & region_flags:
					region_codes.append(region)
			metadata.specific_info['Region-Code'] = region_codes
		except ValueError:
			metadata.specific_info['Region-Code'] = '0x' + region

	#Tempted to reuse wii.parse_ratings, but I might not because it's just a bit different
	rating_values = [int(tag.text) for tag in meta_xml.iter() if tag.tag.startswith('pc_')]
	ratings = [rating & 0b0001_1111 for rating in rating_values if (rating & 0b1000_0000) == 0 and (rating & 0b0100_0000) == 0]
	if ratings:
		try:
			rating = statistics.mode(ratings)
		except statistics.StatisticsError:
			rating = max(ratings)
		metadata.specific_info['Age-Rating'] = rating

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

	short_name = meta_xml.findtext('shortname_en')
	long_name = meta_xml.findtext('longname_en') #Also have ja, fr, de, etc, often zhs/ko/nl/pt/ru/zht is not filled in
	#TODO: Stop being eurocentric and add other languages
	#TODO: Add publisher too
	metadata.add_alternate_name(short_name, 'Short-Name')
	metadata.add_alternate_name(long_name, 'Long-Name')

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

	#This is again where we want a get_sibling_file method I think
	parent_folder = os.path.dirname(rom.path)
	#print(rom.path, parent_folder, os.path.basename(parent_folder))
	if os.path.basename(parent_folder) != 'code':
		#Might be a homebrew game or something, I dunno but either way if we don't have a standard folder structure we have nothing to do here
		try:
			#info.json has the same info? But it's not always there
			add_homebrew_meta_xml_metadata(rom, metadata, ElementTree.parse(os.path.join(parent_folder, 'meta.xml')))
		except FileNotFoundError:
			pass
		homebrew_banner_path = os.path.join(parent_folder, 'icon.png')
		if os.path.isfile(homebrew_banner_path):
			metadata.images['Banner'] = homebrew_banner_path

		return 

	base_dir = os.path.dirname(parent_folder)
	content_dir = os.path.join(base_dir, 'content')
	meta_dir = os.path.join(base_dir, 'meta')
	#We don't really need the content dir for anything right now, but it's probably good to check that we really are looking at a normal folder dump of a Wii U game and not anything weird
	if not (os.path.isdir(content_dir) and os.path.isdir(meta_dir)):
		return

	rom.ignore_name = True
	metadata.add_alternate_name(os.path.basename(base_dir), 'Folder-Name')
	metadata.categories = metadata.categories[:-2]

	#While we are here… using pc_common_metadata engine detect on the content folder almost seems like a good idea too, but it won't accomplish much so far
	if os.path.isfile(os.path.join(parent_folder, 'UnityEngine_dll.rpl')):
		#Unity games on Wii U just have a "Data" folder under content with no executable (because it's over here in code), so our usual detection won't work; not sure about other cross platform engines
		metadata.specific_info['Engine'] = 'Unity'
	
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

def add_wii_u_metadata(game):
	if game.rom.extension == 'rpx':
		add_rpx_metadata(game.rom, game.metadata)
	#We could leverage Cemu to get the meta.xml out of discs with -e <disc.wud> -p meta/meta.xml but that 1) sounds annoying to go back into emulator_config to get the path and such and that might inevitably cause a recursive import 2) pops up a dialog box if the key for the wud isn't there or fails in some other way
