from enum import Flag

from common_types import MediaType
from config.main_config import main_config

categories = {
	#Second item is what we want to set metadata.category to
	'AP': ('Photo App', 'Applications'),
	'AM': ('Music App', 'Applications'),
	'AV': ('Video App', 'Applications'),
	'BV': ('Broadcast Video App', 'Applications'),
	'AT': ('TV App', 'Applications'),
	'WT': ('Web TV App', 'Applications'),
	'HG': ('HDD Game', 'Games'),
	'CB': ('CB', 'Applications'), #Folding@home, etc
	'AS': ('App Store', 'Tools'),
	'HM': ('Home', 'Tools'),
	'SF': ('Shopfront', 'Tools'),
	'2G': ('PS2 Installed Disc', 'Games'),
	'2P': ('PS2 Classics', 'Games'),
	'1P': ('PS1 Classics', 'Games'), #PS3
	'ME': ('PS1 Classics', 'Games'), #PSP
	'MN': ('PSP Minis', 'Games'),
	'PE': ('PSP Remasters', 'Games'),
	'PP': ('Transferable PSP Game', 'Games'), #PS3, doesn't boot
	'EG': ('External Game', 'Games'), #PSP
	'GD': ('Game Data', None), #This shouldn't be bootable
	'2D': ('PS2 Game Data', None), #This shouldn't be bootable
	'SD': ('Save Data', None), #This shouldn't be bootable
	'MG': ('Memory Stick Game', 'Games'),
	'MS': ('Memory Stick Save', None),
	'DG': ('Disc Game', 'Games'), #PS3
	'UG': ('UMD Game', 'Games'),
	'UV': ('UMD Video', 'Multimedia'),
	#UMD Audio is in here, presumably
	'PG': ('PSP Update', None),
	'MA': ('Memory Stick App', 'Applications'),
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
	1: 'American English',

	#PS2/PSP/PS3/Vita/PS4 only:
	2: 'French',
	3: 'Spanish',
	4: 'German',
	5: 'Italian',
	6: 'Dutch',
	7: 'Portugese',
	8: 'Russian',
	9: 'Korean',
	10: 'Traditional Chinese',
	11: 'Simplified Chinese',

	#PS3/Vita/PS4 only:
	12: 'Finnish',
	13: 'Swedish',
	14: 'Danish',
	15: 'Norwegian',
	16: 'Polish',
	17: 'Brazilian Portugese',
	18: 'British English',
	19: 'Turkish',

	#PS4 only:
	20: 'Latin American Spanish',
	21: 'Arabic',
	22: 'Canadian French',
	23: 'Czech',
	24: 'Hungarian',
	25: 'Greek',
	26: 'Romanian',
	27: 'Thai',
	28: 'Vietnamese',
	29: 'Indonesian',

}

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

def parse_param_sfo(rom, metadata, param_sfo):
	magic = param_sfo[:4]
	if magic != b'\x00PSF':
		return
	for key, value in convert_sfo(param_sfo).items():
		if key == 'DISC_ID':
			if value != 'UCJS10041':
				#That one's used by all the PSP homebrews
				metadata.product_code = value
		elif key == 'TITLE_ID':
			#PS3 uses this instead I guess
			metadata.product_code = value
		elif key == 'DISC_NUMBER':
			metadata.disc_number = value
		elif key == 'DISC_TOTAL':
			metadata.disc_total = value
		elif key == 'TITLE':
			metadata.add_alternate_name(value, 'Banner-Title')
		elif len(key) == 8 and key[:5] == 'TITLE' and key[-2:].isdigit():
			lang_id = int(key[-2:])
			prefix = title_languages.get(lang_id)
			name_name = 'Banner-Title'
			if prefix:
				name_name = prefix.replace(' ', '-') + '-' + name_name
			metadata.add_alternate_name(value, name_name)
		elif key == 'PARENTAL_LEVEL':
			#Seems this doesn't actually mean anything by itself, and is Sony's own rating system, so don't try and think about it too much
			metadata.specific_info['Parental-Level'] = value
		elif key == 'CATEGORY':
			#This is a two letter code which generally means something like "Memory stick game" "Update" "PS1 Classics", see ROMniscience notes
			cat = categories.get(value)
			if cat:
				if not cat[1]:
					metadata.specific_info['Should-Not-Be-Bootable'] = True
				metadata.specific_info['PlayStation-Category'] = cat[0]
				if not metadata.categories or (len(metadata.categories) == 1 and metadata.categories[0] == metadata.platform):
					metadata.categories = [cat[1]]
			else:
				if main_config.debug:
					print(rom.path, 'has unknown category', value)
		elif key in ('DISC_VERSION', 'APP_VER'):
			if value[0] != 'v':
				value = 'v' + value
			metadata.specific_info['Version'] = value
		elif key == 'VERSION':
			metadata.specific_info['Revision'] = value
		elif key == 'LICENSE':
			metadata.descriptions['License'] = value
		elif key == 'BOOTABLE':
			if value == 0:
				metadata.specific_info['Bootable'] = False
				#Does not seem to ever be set to anything??
		elif key == 'CONTENT_ID':
			metadata.specific_info['Content-ID'] = value
		elif key == 'USE_USB':
			metadata.specific_info['Uses-USB'] = value != 0
		elif key in ('PSP_SYSTEM_VER', 'PS3_SYSTEM_VER'):
			metadata.specific_info['Required-Firmware'] = value
		elif key == 'ATTRIBUTE':
			if value:
				try:
					flags = AttributeFlags(value)
					if flags & AttributeFlags.MoveControllerEnabled:
						metadata.specific_info['Uses-Move-Controller'] = True
					#metadata.specific_info['Attribute-Flags'] = flags

				except ValueError:
					#metadata.specific_info['Attribute-Flags'] = hex(value)
					if main_config.debug:
						print(rom.path, 'has funny attributes flag', hex(value))
		elif key == 'RESOLUTION':
			try:
				metadata.specific_info['Supported-Resolutions'] = [res[1:] for res in str(Resolutions(value))[12:].split('|')]
			except ValueError:
				if main_config.debug:
					print(rom.path, 'has funny resolution flag', hex(value))
		elif key == 'SOUND_FORMAT':
			try:
				metadata.specific_info['Supported-Sound-Formats'] = [res.lstrip('_').replace('_', '.') for res in str(SoundFormats(value))[13:].split('|')]
			except ValueError:
				if main_config.debug:
					print(rom.path, 'has funny sound format flag', hex(value))
		elif key in ('MEMSIZE', 'REGION', 'HRKGMP_VER', 'NP_COMMUNICATION_ID'):
			#These are known, but not necessarily useful to us or we just don't feel like putting it in the metadata or otherwise doing anything with it at this point
			#MEMSIZE: PSP, 1 if game uses extra RAM?
			#REGION: Seems to always be 32768 (is anything region locked?) and also only on PSP??
			#HRKGMP_VER = ??? (19)
			#NP_COMMUNICATION_ID = PS3, ID used for online features I guess, also the subdirectory of TROPDIR containing TROPHY.TRP
			#print('ooo', rom.path, key, value)
			pass
		else:
			if main_config.debug:
				print(rom.path, 'has unknown param.sfo value', key, value)

def parse_product_code(metadata):
	if len(metadata.product_code) == 9 and metadata.product_code[:4].isalpha() and metadata.product_code[-5:].isdigit():
		if metadata.product_code.startswith(('B', 'P', 'S', 'X', 'U')):
			metadata.media_type = MediaType.OpticalDisc
			if metadata.product_code[1] == 'C':
				metadata.publisher = 'Sony'
		if metadata.product_code.startswith('V'):
			metadata.media_type = MediaType.Cartridge
			if metadata.product_code[1] == 'C':
				metadata.publisher = 'Sony'
		if metadata.product_code.startswith('NP'):
			metadata.media_type = MediaType.Digital
			if metadata.product_code[3] in ('A', 'C', 'F', 'G', 'I', 'K', 'W', 'X'):
				metadata.publisher = 'Sony'
