import subprocess
import xml.etree.ElementTree as ElementTree
import os

from metadata import CPUInfo, ScreenInfo

def consistentify_manufacturer(manufacturer):
	#Sometimes, MAME uses two different variations on what is the same exact company. Or formats the name in a way that nobody else does anywhere else.
	#I'm not going to count regional branches of a company, though.
	#TODO: Are ATW > ATW USA Inc. the same or a regional branch?
	#Should NEC Avenue and NEC Home Electronics just be called NEC?
	#Should Sony Computer Entertainment Inc and Sony Imagesoft be just Sony?
	return {
		'Bally Gaming Co.': 'Bally',
		'BPS': 'Bullet-Proof Software', #I hope nobody else uses that acronym
		'Data East Corporation': 'Data East',
		'Entex Industries': 'Entex',
		'HAL Kenkyuujo': 'HAL', #Literally "HAL Laboratory"
		'HAL Laboratory': 'HAL',
		'Hudson': 'Hudson Soft',
		'Kaneko Elc. Co.': 'Kaneko',
		'MicroCabin': 'Micro Cabin', #Annoying alternate spelling because they officially use both just to be annoying
		'Nihon Telenet': 'Telenet', #I guess
		'Omori Electric Co., Ltd.': 'Omori',
		'Palm Inc': 'Palm',
		'Sigma Enterprises Inc.': 'Sigma',
		'Square': 'Squaresoft', #Which is the frickin' right one?
		'Taito Corporation': 'Taito',
		'Taito Corporation Japan': 'Taito',
		'Taito America Corporation': 'Taito America',
		'UA Ltd.': 'UA Limited', #MAME uses the former (for Arcadia 2001 lists), Stella uses the latter in its database

		#For some reason, some Japanese computer software lists have the Japanese name and then the English one in brackets. Everywhere else the English name is used even when the whole thing is Japanese. Anyway, fine, I can deal with that
		'B·P·S (Bullet-Proof Software)': 'Bullet-Proof Software',
		'アイレム (Irem)': 'Irem',
		'アスキー (ASCII)': 'ASCII',
		'イマジニア (Imagineer)': 'Imagineer',
		'エニックス (Enix)': 'Enix',
		'カプコン (Capcom)': 'Capcom',
		'コナミ (Konami)': 'Konami',
		'システムサコム (System Sacom)': 'System Sacom',
		'システムソフト (System Soft)': 'System Soft',
		'シャープ (Sharp)': 'Sharp',
		'スタークラフト (Starcraft)': 'Starcraft',
		'ソフトプロ (Soft Pro)': 'Soft Pro',
		'デービーソフト (dB-Soft)': 'dB-Soft',
		'ハドソン (Hudson Soft)': 'Hudson Soft',
		'ブラザー工業 (Brother Kougyou)': 'Brother Kougyou',
		'ホームデータ (Home Data)': 'Home Data',
		'マカダミアソフト (Macadamia Soft)': 'Macadamia Soft',
		'日本ファルコム (Nihon Falcom)': 'Nihon Falcom',
		'電波新聞社 (Dempa Shinbunsha)': 'Dempa Shinbunsha',

		#These ones are basically just typos...
		'enix': 'Enix',
		'GTC Inc.': 'GTC Inc',
		'Pack-In-Video': 'Pack-In Video',
	}.get(manufacturer, manufacturer)

def find_in_software_lists(software_lists, crc=None, sha1=None):
	#TODO: Handle hash collisions. Could happen, even if we're narrowing down to specific software lists
	for software_list in software_lists:
		for software in software_list.findall('software'):
			for part in software.findall('part'):
				#There will be multiple parts sometimes, like if there's multiple floppy disks for one game (will have name = flop1, flop2, etc)
				#diskarea is used instead of dataarea seemingly for CDs or anything else that MAME would use a .chd for in its software list
				for data_area in part.findall('dataarea'):
					roms = data_area.findall('rom')
					if not roms:
						#Ignore data areas such as "sram" that don't have any ROMs associated with them.
						#Note that data area's name attribute can be anything like "rom" or "flop" depending on the kind of media, but the element inside will always be called "rom"
						continue
					for rom in roms:
						if sha1:
							if 'sha1' in rom.attrib and rom.attrib['sha1'] == sha1:
								return software, part
						if crc:
							if 'crc' in rom.attrib and rom.attrib['crc'] == crc:
								return software, part

	return None, None

def get_software_lists_by_names(names):
	if not names:
		return []
	return [software_list for software_list in [get_software_list_by_name(name) for name in names] if software_list]

def get_software_list_by_name(name):
	hash_path = '/usr/lib/mame/hash'
	#TODO: Get this from MAME config instead
	list_path = os.path.join(hash_path, name + '.xml')
	if not os.path.isfile(list_path):
		return None
	return ElementTree.parse(list_path)

def get_full_name(driver_name):
	xml = get_mame_xml(driver_name)
	if not xml:
		return None

	return xml.find('machine').findtext('description')

def lookup_system_cpu(driver_name):
	xml = get_mame_xml(driver_name)
	if not xml:
		return None
	machine = xml.find('machine')
	if not machine:
		return None

	main_cpu = find_main_cpu(machine)
	if main_cpu is not None: #"if main_cpu: doesn't work. Frig! Why not! Wanker! Sodding bollocks!
		cpu_info = CPUInfo()
		cpu_info.load_from_xml(main_cpu)

		return cpu_info

	return None

def lookup_system_displays(driver_name):
	xml = get_mame_xml(driver_name)
	if not xml:
		return None
	machine = xml.find('machine')
	if not machine:
		return None

	displays = machine.findall('display')
	screen_info = ScreenInfo()
	screen_info.load_from_xml_list(displays)
	return screen_info

_get_xml_cache = {}
def get_mame_xml(driver):
	if driver in _get_xml_cache:
		return _get_xml_cache[driver]

	process = subprocess.run(['mame', '-listxml', driver], stdout=subprocess.PIPE)
	status = process.returncode
	output = process.stdout
	if status != 0:
		print('Fucking hell ' + driver)
		return None

	xml = ElementTree.fromstring(output)
	_get_xml_cache[driver] = xml
	return xml

def find_main_cpu(machine_xml):
	for chip in machine_xml.findall('chip'):
		tag = chip.attrib['tag']
		if tag == 'maincpu' or tag == 'mainpcb:maincpu':
			return chip

	#If no maincpu, just grab the first CPU chip
	for chip in machine_xml.findall('chip'):
		if chip.attrib['type'] == 'cpu':
			return chip

	#Alto I and HP 2100 have no chips, apparently.  Huh?  Oh well
	return None
