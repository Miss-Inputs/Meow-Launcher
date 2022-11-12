import logging
from collections.abc import Mapping
from enum import Flag
from typing import TYPE_CHECKING, Any, NamedTuple, Union, cast

from meowlauncher.common_types import MediaType
from meowlauncher.util.name_utils import fix_name

if TYPE_CHECKING:
	from meowlauncher.metadata import Metadata

logger = logging.getLogger(__name__)

class PlayStationCategory(NamedTuple):
	cat: str
	metadata_category: str | None #What we might like to set metadata.categories to

categories = {
	'AP': PlayStationCategory('Photo App', 'Applications'),
	'AM': PlayStationCategory('Music App', 'Applications'),
	'AV': PlayStationCategory('Video App', 'Applications'),
	'BV': PlayStationCategory('Broadcast Video App', 'Applications'),
	'AT': PlayStationCategory('TV App', 'Applications'),
	'WT': PlayStationCategory('Web TV App', 'Applications'),
	'HG': PlayStationCategory('HDD Game', 'Games'),
	'CB': PlayStationCategory('Network App', 'Applications'), #Folding@home, etc, RPCS3 says this is what CB means and I guess homebrew apps that are like web browsers etc use it
	'AS': PlayStationCategory('App Store', 'Tools'),
	'HM': PlayStationCategory('Home', 'Tools'),
	'SF': PlayStationCategory('Shopfront', 'Tools'),
	'2G': PlayStationCategory('PS2 Installed Disc', 'Games'),
	'2P': PlayStationCategory('PS2 Classics', 'Games'),
	'1P': PlayStationCategory('PS1 Classics', 'Games'), #PS3
	'ME': PlayStationCategory('PS1 Classics', 'Games'), #PSP
	'MN': PlayStationCategory('PSP Minis', 'Games'),
	'PE': PlayStationCategory('PSP Remasters', 'Games'),
	'PP': PlayStationCategory('Transferable PSP Game', 'Games'), #PS3, doesn't boot
	'EG': PlayStationCategory('External Game', 'Games'), #PSP
	'GD': PlayStationCategory('Game Data', None), #This shouldn't be bootable
	'2D': PlayStationCategory('PS2 Game Data', None), #This shouldn't be bootable
	'SD': PlayStationCategory('Save Data', None), #This shouldn't be bootable
	'MG': PlayStationCategory('Memory Stick Game', 'Games'),
	'MS': PlayStationCategory('Memory Stick Save', None),
	'DG': PlayStationCategory('Disc Game', 'Games'), #PS3
	'UG': PlayStationCategory('UMD Game', 'Games'),
	'UV': PlayStationCategory('UMD Video', 'Multimedia'),
	#UMD Audio is in here, presumably
	'PG': PlayStationCategory('PSP Update', None),
	'MA': PlayStationCategory('Memory Stick App', 'Applications'),

	#Seen in PARAM.SFX in subdirs of PS3_EXTRA:
	#IP = main package for PSP remaster?
	#VI = video file?
}

class AttributeFlags(Flag):
	PSPRemotePlay = 1
	PSPExport = 2
	PSPRemotePlayV2 = 4
	XMBForcedEnabled = 8
	XMBDisabled = 0x10
	XMBBackgroundMusic = 0x20
	SystemVoiceChat = 0x40
	VitaRemotePlay = 0x80
	MoveControllerWarning = 0x100 #These three do not actually show if a given controller is used, they just determine if warnings should be shown
	NavigationControllerWarning = 0x200
	EyeCamWarning = 0x400
	MoveCalibrationNotification = 0x800
	Stereoscopic3DWarning = 0x1000
	UnknownFlagInPSNowBeta = 0x2000
	InstallDisc = 0x10000
	InstallPackages = 0x20000
	GamePurchaseEnabled = 0x80000
	PCEngine = 0x200000 #Okay, so that's what the PS3 dev wiki calls it. But if Neo Geo games have it then it probably means "emulated" or whatever wording might be used
	LicenseLogoDisabled = 0x400000
	MoveControllerEnabled = 0x800000
	NeoGeo = 0x4000000

class Resolutions(Flag):
	_640x480 = 1
	_768x576 = 2
	_1280x720 = 4
	_1920x1080 = 8
	_854x480 = 16
	_1024x576 = 32

class SoundFormats(Flag):
	Stereo = 1
	Encoded = 2
	_5_1 = 4
	_7_1 = 16
	DolbyDigital5_1 = 256
	DTS5_1 = 512

title_languages = {
	0: 'Japanese',
	1: 'English (American)',

	#PS2/PSP/PS3/Vita/PS4 only:
	2: 'French',
	3: 'Spanish',
	4: 'German',
	5: 'Italian',
	6: 'Dutch',
	7: 'Portuguese',
	8: 'Russian',
	9: 'Korean',
	10: 'Chinese (Traditional)',
	11: 'Chinese (Simplified)',

	#PS3/Vita/PS4 only:
	12: 'Finnish',
	13: 'Swedish',
	14: 'Danish',
	15: 'Norwegian',
	16: 'Polish',
	17: 'Portuguese (Brazilian)',
	18: 'English (British)',
	19: 'Turkish',

	#PS4 only:
	20: 'Spanish (Latin American)',
	21: 'Arabic',
	22: 'French (Canadian)',
	23: 'Czech',
	24: 'Hungarian',
	25: 'Greek',
	26: 'Romanian',
	27: 'Thai',
	28: 'Vietnamese',
	29: 'Indonesian',

}

SFOValueType = Union[str, int] #Not sure if there is more than that…

def _convert_sfo(sfo: bytes, rom_path_for_warning: Any=None) -> Mapping[bytes, SFOValueType]:
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

		key = sfo[key_offset:].split(b'\x00', 1)[0]

		value: SFOValueType
		try:
			if data_format == 4: #UTF8 not null terminated
				value = sfo[data_offset:data_offset+data_used_length].decode('utf8')
			elif data_format == 0x204: #UTF8 null terminated
				value = sfo[data_offset:].split(b'\x00', 1)[0].decode('utf8')
			elif data_format == 0x404: #int32
				value = int.from_bytes(sfo[data_offset:data_offset+4], 'little')
			else:
				logger.info('Whoops unknown format %s in convert_sfo for %s', hex(data_format), rom_path_for_warning)
				continue
		except UnicodeDecodeError:
			logger.info('Incorrect sfo value in %s', rom_path_for_warning, exc_info=True)
			continue

		d[key] = value
	return d

def parse_param_sfo_kv(object_for_warning: Any, metadata: 'Metadata', key: bytes, value: SFOValueType) -> None:
	if key == b'DISC_ID':
		if value != 'UCJS10041':
			#That one's used by all the PSP homebrews
			metadata.product_code = cast(str, value)
	elif key == b'TITLE_ID':
		#PS3 uses this instead I guess
		metadata.product_code = cast(str, value)
	elif key == b'DISC_NUMBER':
		metadata.disc_number = cast(int, value)
	elif key == b'DISC_TOTAL':
		metadata.disc_total = cast(int, value)
	elif key == b'TITLE':
		metadata.add_alternate_name(fix_name(cast(str, value).replace('\n', ': ')), 'Banner Title')
	elif len(key) == 8 and key[:5] == b'TITLE' and key[-2:].isdigit():
		lang_id = int(key[-2:])
		prefix = title_languages.get(lang_id)
		name_name = 'Banner Title'
		if prefix:
			name_name = prefix + name_name
		metadata.add_alternate_name(fix_name(cast(str, value).replace('\n', ': ')), name_name)
	elif key == b'PARENTAL_LEVEL':
		#Seems this doesn't actually mean anything by itself, and is Sony's own rating system, so don't try and think about it too much
		metadata.specific_info['Parental Level'] = value
	elif key == b'CATEGORY':
		#This is a two letter code which generally means something like "Memory stick game" "Update" "PS1 Classics", see ROMniscience notes
		cat = categories.get(cast(str, value))
		if cat:
			metadata.specific_info['PlayStation Category'] = cat.cat
			if cat.metadata_category is not None:
				if not metadata.categories or (len(metadata.categories) == 1 and metadata.categories[0] == metadata.platform):
					metadata.categories = [cat.metadata_category]
			else:
				metadata.specific_info['Bootable?'] = False
		else:
			logger.info('%s has unknown category %s', object_for_warning, value)
	elif key in {b'DISC_VERSION', b'APP_VER'}:
		if cast(str, value)[0] != 'v':
			value = 'v' + cast(str, value)
		metadata.specific_info['Version'] = value
	elif key == b'VERSION':
		metadata.specific_info['Revision'] = value
	elif key == b'LICENSE':
		metadata.descriptions['License'] = cast(str, value)
	elif key == b'BOOTABLE':
		if value == 0:
			metadata.specific_info['Bootable?'] = False
			#Does not seem to ever be set to anything??
	elif key == b'CONTENT_ID':
		metadata.specific_info['Content ID'] = value
	elif key == b'USE_USB':
		metadata.specific_info['Uses USB?'] = value != 0
	elif key in {b'PSP_SYSTEM_VER', b'PS3_SYSTEM_VER'}:
		metadata.specific_info['Required Firmware'] = value
	elif key == b'ATTRIBUTE':
		if value:
			try:
				flags = AttributeFlags(value)
				if flags & AttributeFlags.MoveControllerEnabled:
					metadata.specific_info['Uses Move Controller?'] = True
				#metadata.specific_info['Attribute Flags'] = flags

			except ValueError:
				#metadata.specific_info['Attribute Flags'] = hex(value)
				logger.info('%s has funny attributes flag %s', object_for_warning, hex(cast(int, value)))
	elif key == b'RESOLUTION':
		try:
			metadata.specific_info['Display Resolution'] = {res[1:] for res in str(Resolutions(value))[12:].split('|')}
		except ValueError:
			logger.info('%s has funny resolution flag %s', object_for_warning, hex(cast(int, value)))
	elif key == b'SOUND_FORMAT':
		try:
			metadata.specific_info['Supported Sound Formats'] = {res.lstrip('_').replace('_', '.') for res in str(SoundFormats(value))[13:].split('|')}
		except ValueError:
			logger.info('%s has funny sound format flag %s', object_for_warning, hex(cast(int, value)))
	elif key in {b'MEMSIZE', b'REGION', b'HRKGMP_VER', b'NP_COMMUNICATION_ID'}:
		#These are known, but not necessarily useful to us or we just don't feel like putting it in the metadata or otherwise doing anything with it at this point
		#MEMSIZE: PSP, 1 if game uses extra RAM?
		#REGION: Seems to always be 32768 (is anything region locked?) and also only on PSP??
		#HRKGMP_VER = ??? (19)
		#NP_COMMUNICATION_ID = PS3, ID used for online features I guess, also the subdirectory of TROPDIR containing TROPHY.TRP
		logger.debug('Key that may be more interesting than I currently think: path = %s key = %s value = %s', object_for_warning, key, value)
	else:
		logger.info('%s has unknown param.sfo key %s with value %s', object_for_warning, key, value)

def parse_param_sfo(object_for_warning: Any, metadata: 'Metadata', param_sfo: bytes) -> None:
	magic = param_sfo[:4]
	if magic != b'\x00PSF':
		return
	for key, value in _convert_sfo(param_sfo, object_for_warning).items():
		parse_param_sfo_kv(object_for_warning, metadata, key, value)

def parse_product_code(metadata: 'Metadata', product_code: str) -> None:
	if len(product_code) == 9 and product_code[:4].isalpha() and product_code[-5:].isdigit():
		if product_code.startswith(('B', 'P', 'S', 'X', 'U')):
			metadata.media_type = MediaType.OpticalDisc
			if product_code[1] == 'C':
				metadata.publisher = 'Sony'
		elif product_code.startswith('V'):
			metadata.media_type = MediaType.Cartridge
			if product_code[1] == 'C':
				metadata.publisher = 'Sony'
		elif product_code.startswith('NP'):
			metadata.media_type = MediaType.Digital
			if product_code[3] in {'A', 'C', 'F', 'G', 'I', 'K', 'W', 'X'}:
				metadata.publisher = 'Sony'
