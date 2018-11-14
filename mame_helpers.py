import subprocess
import xml.etree.ElementTree as ElementTree
import re
import os

from metadata import CPUInfo, ScreenInfo

def consistentify_manufacturer(manufacturer):
	#Sometimes, MAME uses two different variations on what is the same exact company. Or formats the name in a way that nobody else does anywhere else.
	#I'm not going to count regional branches of a company, though. Just kinda feel like I should leave that stuff untouched.
	#Sometimes I don't know which out of the two variations is what I should go with... I just want only one of them. If any people out there are experts on the field of company names, then by all means tell me off.
	#If only there was some consistent guidelines to follow in this, and nintendo_common/sega_common/wonderswan etc...

	#Anyway. Some of these are bit... contentious? Is that the right word? Like, some of these are definitely different ways of spelling the same company and that's definitely a valid thing to deal with, but then some of these might well just be different brands used by the same company, because companies are weird like that. So at some point I'll probably need to clean this up. Hmm...

	#Maybe I should remove ", Inc." "Co Ltd." at the end of stuff automatically, and... hmm

	#TODO: Are ATW > ATW USA Inc. the same or a regional branch?
	#Should NEC Avenue just be called NEC?
	#Should Sony Computer Entertainment Inc and Sony Imagesoft be just Sony?
	#Toshiba EMI > Toshiba?
	#Are CBS Electronics and CBS Software the same? Seems like they're both owned by CBS the American TV company, the former is for various Atari 2600/5200/7800 games they published and distributing the ColecoVision outside USA; and the latter is basically licensed Sesame Street games?
	#Are Fox Interactive, Fox Video Games, 20th Century Fox all the same?
	#Human == Human Amusement?
	#Ultra, Ultra Games, Konami (Ultra Games)?
	#Universal == Universal Video Games?
	#BBC Worldwide == BBC Multimedia? I mean they're obviously both the BBC
	#Empire Entertainment == Empire Interactive?
	#The SNES game Super Godzilla (USA) has a publisher of literally "Super Godzilla". Wait what? That can't be right. Should be Toho right? Same with Tetris (Japan) for Megadrive. Unless they meant The Tetris Company there.
	#Leave Atari Games > Atari and Midway Games > Midway alone, because if I try to comperehend the timeline of which is what and who owned the rights to which brand name and who owned who at any given time, I would die of confusion
	#Marvelous Entertainment and Marvelous Interactive also are different (due to mergers) and I gotta remember that
	return {
		'20th Century Fox Video Games': '20th Century Fox',
		'Absolute': 'Absolute Entertainment',
		'Absolute Entertainment, Inc': 'Absolute Entertainment',
		'Absolute Entertainment, Inc.': 'Absolute Entertainment',
		'Acclaim Entertainment': 'Acclaim',
		'Alpha Denshi Co.': 'ADK', #Renamed in 1993, but let's not make this confusing
		'American Softworks Company': 'American Softworks',
		'Apple Computer, Inc.': 'Apple Computer',
		'ASCII Entertainment': 'ASCII',
		'Atarisoft': 'Atari', #Atarisoft is just a brand name and not an actual company, so I guess I'll do this
		'Bally Gaming Co.': 'Bally',
		'BPS': 'Bullet-Proof Software', #I hope nobody else uses that acronym
		'Brøderbund Software Inc': 'Brøderbund',
		'California Pacific Computer': 'California Pacific',
		'Coconuts Japan Entertainment': 'Coconuts Japan',
		'Creative Software': 'Creative', #Gonna guess this isn't the sound card company. Would be an interesting predicament if they made software that was in the software lists, huh
		'Cryo': 'Cryo Interactive',
		'Data East Corporation': 'Data East',
		'Daiwon C & A': 'Daiwon C&A Holdings', #Yeah, maybe the nintendo_common version of the name sucks, actually...
		'Dempa Shinbunsha': 'Dempa',
		'Disney Interactive': 'Disney',
		'Disney Interactive Studios': 'Disney',
		'Disney Software': 'Disney',
		'Dreamworks Games': 'DreamWorks',
		'DSI Games': 'Destination Software', #They kinda go by both, actually...
		'dtp Entertainment': 'Digital Tainment Pool', #Yeah, they also go by both...
		'Eidos Interactive': 'Eidos',
		'Elite': 'Elite Systems',
		'Entex Industries': 'Entex',
		'First Star': 'First Star Software',
		'Gremlin Interactive': 'Gremlin Graphics',
		'HAL Kenkyuujo': 'HAL', #Literally "HAL Laboratory"
		'HAL Laboratory': 'HAL',
		'Hasbro Interactive': 'Hasbro',
		'HiCom': 'Hi-Com',
		'Hot-B Co., Ltd.': 'Hot-B',
		'Hudson': 'Hudson Soft',
		'Human Entertainment': 'Human',
		'International Business Machines': 'IBM',
		'INTV Corp.': 'INTV',
		'JoWooD Entertainment AG': 'JoWooD Entertainment',
		'Kaneko Elc. Co.': 'Kaneko',
		'K-Tel Vision': 'K-Tel',
		'Laser Beam': 'Laser Beam Entertainment',
		'LEGO Media': 'Lego',
		'Mattel Electronics': 'Mattel',
		'Mattel Interactive': 'Mattel',
		'Mattel Media': 'Mattel',
		'MicroCabin': 'Micro Cabin', #Annoying alternate spelling because they officially use both just to be annoying
		'Microlab': 'Micro Lab',
		'Microprose Games Inc.': 'MicroProse',
		'NEC Home Electronics': 'NEC',
		'Nihon Telenet': 'Telenet', #I guess
		'Nihon Bussan': 'Nichibutsu', #C'mon, use their preferred name
		'Ocean Software': 'Ocean',
		'Omage Micott, Inc.': 'Omega Micott', #I have a feeling I'm the one who's wrong here. Never did quality check the Wonderswan licensees
		'Omori Electric Co., Ltd.': 'Omori',
		'Palm Inc': 'Palm',
		'Playmates Interactive': 'Playmates',
		'PonyCa': 'Pony Canyon',
		'ProSoft': 'Prosoft',
		'Sammy Entertainment': 'Sammy',
		'Seta Corporation': 'Seta',
		'Sierra Entertainment': 'Sierra',
		'Sierra On-Line': 'Sierra',
		'Sigma Enterprises Inc.': 'Sigma', #Every time I see this line I keep thinking "sigma balls", just thought you should know
		'Software Toolworks': 'The Software Toolworks', #It doesn't seem right that the "correct" one is the latter, but it's used more often, so I guess it is
		'Spinnaker Software': 'Spinnaker',
		'Spinnaker Software Corp': 'Spinnaker',
		'Square': 'Squaresoft', #Which is the frickin' right one?
		'Sunrise Software': 'Sunrise',
		'Taito Corporation': 'Taito',
		'Taito Corporation Japan': 'Taito',
		'Taito America Corporation': 'Taito America',
		'TecMagik Entertainment Ltd.': 'TecMagik',
		'T*HQ': 'THQ', #Why.
		'Titus Software': 'Titus',
		'UA Ltd.': 'UA Limited', #MAME uses the former (for Arcadia 2001 lists), Stella uses the latter in its database
		'Ubi Soft': 'Ubisoft', #I hate that they used to spell their name with a space so this is valid. But then, don't we all hate Ubisoft for one reason or another?
		'Ultra Games': 'Konami (Ultra Games)', #This is questionable to format it like this, but... I'll contemplate which one is better some other time
		'V.Fame': 'Vast Fame',
		'Viacom New Media': 'Viacom',
		'Video System Co.': 'Video System',
		'Visco Corporation': 'Visco',
		'Virgin Games': 'Virgin',
		'Virgin Interactive': 'Virgin',
		'Vivendi Universal': 'Vivendi', #Probably kinda wrong, but ehhh
		'Williams Entertainment': 'Williams',

		#For some reason, some Japanese computer software lists have the Japanese name and then the English one in brackets. Everywhere else the English name is used even when the whole thing is Japanese. Anyway I guess we just want the English name then, because otherwise for consistency, I'd have to convert every single English name into Japanese
		'B·P·S (Bullet-Proof Software)': 'Bullet-Proof Software',
		'アイレム (Irem)': 'Irem',
		'アスキー (ASCII)': 'ASCII',
		'イマジニア (Imagineer)': 'Imagineer',
		'エニックス (Enix)': 'Enix',
		'カプコン (Capcom)': 'Capcom',
		'コナミ (Konami)': 'Konami',
		'コンプティーク (Comptiq)': 'Comptiq',
		'システムサコム (System Sacom)': 'System Sacom',
		'システムソフト (System Soft)': 'System Soft',
		'シャープ (Sharp)': 'Sharp',
		'シンキングラビット (Thinking Rabbit)': 'Thinking Rabbit',
		'スタークラフト (Starcraft)': 'Starcraft',
		'ソフトプロ (Soft Pro)': 'Soft Pro',
		'デービーソフト (dB-Soft)': 'dB-Soft',
		'ニデコム (Nidecom)': 'Nidecom',
		'パックスエレクトロニカ (Pax Electronica)': 'Pax Electronica',
		'ハドソン (Hudson Soft)': 'Hudson Soft',
		'ブラザー工業 (Brother Kougyou)': 'Brother Kougyou',
		'ホームデータ (Home Data)': 'Home Data',
		'ポニカ (Pony Canyon)': 'Pony Canyon',
		'ポニカ (PonyCa)': 'Pony Canyon',
		'マイクロネット (Micronet)': 'Micronet',
		'マカダミアソフト (Macadamia Soft)': 'Macadamia Soft',
		'日本ソフトバンク (Nihon SoftBank)': 'Nihon SoftBank',
		'日本ファルコム (Nihon Falcom)': 'Nihon Falcom',
		'電波新聞社 (Dempa Shinbunsha)': 'Dempa',

		#These ones are probably just typos... I wonder if I can just like, send a pull request or something. But then I might actually be wrong
		'BEC': 'Bec',
		'Commonweaalth': 'Commonwealth',
		'Connonwealth': 'Commonwealth',
		'Dreamworks': 'DreamWorks',
		'Elite System': 'Elite Systems',
		'enix': 'Enix',
		'EPYX': 'Epyx',
		'GTC Inc.': 'GTC Inc',
		'Hi Tech Expressions': 'Hi-Tech Expressions',
		'Jungle\'s Soft - Ultimate Products (HK) Ltd': 'Jungle Soft - Ultimate Products (HK) Ltd',
		'Microprose': 'MicroProse',
		'Mindscapce': 'Mindscape', #Yeah okay, that _definitely_ is a typo
		'Pack-In-Video': 'Pack-In Video',
		'SONY': 'Sony',
		'SpectraVideo': 'Spectravideo',
		'Take Two Interactive': 'Take-Two Interactive',
		'VAP': 'Vap',

		'unknown': '<unknown>', #This shows up in sv8000 software list, so it might actually just be Bandai, but when you presume you make a pres out of u and me, so we'll just lump it in with the other unknowns
	}.get(manufacturer, manufacturer)


mame_config_comment = re.compile(r'#.+$')
mame_config_line = re.compile(r'^(?P<key>\w+)\s+(?P<value>.+)$')
mame_config_values = re.compile(r'(".+"|[^;]+)') #Not sure if single quotes are okay too...
class MameConfigFile():
	def __init__(self, path):
		self.path = path
		self.settings = {}

		with open(path, 'rt') as f:
			for line in f.readlines():
				line = mame_config_comment.sub('', line)
				line = line.strip()

				if not line:
					continue

				match = mame_config_line.match(line)
				if match:
					key = match['key']
					value = mame_config_values.findall(match['value'])
					self.settings[key] = value

def get_mame_config():
	path = os.path.expanduser('~/.mame/mame.ini')
	if os.path.isfile(path):
		return MameConfigFile(path)
	return None

def get_mame_ui_config():
	path = os.path.expanduser('~/.mame/ui.ini')
	if os.path.isfile(path):
		return MameConfigFile(path)
	return None

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
