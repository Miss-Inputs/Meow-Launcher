import subprocess
import xml.etree.ElementTree as ElementTree

from metadata import CPUInfo, ScreenInfo

def consistentify_manufacturer(manufacturer):
	#Sometimes, MAME uses two different variations on what is the same exact company. Or formats the name in a way that nobody else does anywhere else.
	#I'm not going to count regional branches of a company, though.
	#Sometimes I don't know which out of the two variations is what I should go with... I just want only one of them. If any people out there are experts on the field of company names, then by all means tell me off.
	#If only there was some consistent guidelines to follow in this, and nintendo_common/sega_common/wonderswan etc...

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
		'ASCII Entertainment': 'ASCII',
		'Atarisoft': 'Atari', #Atarisoft is just a brand name and not an actual company, so I guess I'll do this
		'Bally Gaming Co.': 'Bally',
		'BPS': 'Bullet-Proof Software', #I hope nobody else uses that acronym
		'Brøderbund Software Inc': 'Brøderbund',
		'Coconuts Japan Entertainment': 'Coconuts Japan',
		'Creative Software': 'Creative', #Gonna guess this isn't the sound card company. Would be an interesting predicament if they made software that was in the software lists, huh
		'Cryo': 'Cryo Interactive',
		'Data East Corporation': 'Data East',
		'Daiwon C & A': 'Daiwon C&A Holdings', #Yeah, maybe the nintendo_common version of the name sucks, actually...
		'Dempa Shinbunsha': 'Dempa',
		'Disney Interactive': 'Disney',
		'Disney Interactive Studios': 'Disney',
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
		'Hudson': 'Hudson Soft',
		'Human Entertainment': 'Human',
		'International Business Machines': 'IBM',
		'INTV Corp.': 'INTV',
		'JoWooD Entertainment AG': 'JoWooD Entertainment',
		'Kaneko Elc. Co.': 'Kaneko',
		'Laser Beam': 'Laser Beam Entertainment',
		'LEGO Media': 'Lego',
		'Mattel Electronics': 'Mattel',
		'Mattel Interactive': 'Mattel',
		'Mattel Media': 'Mattel',
		'MicroCabin': 'Micro Cabin', #Annoying alternate spelling because they officially use both just to be annoying
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
		'Square': 'Squaresoft', #Which is the frickin' right one?
		'Taito Corporation': 'Taito',
		'Taito Corporation Japan': 'Taito',
		'Taito America Corporation': 'Taito America',
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
		'電波新聞社 (Dempa Shinbunsha)': 'Dempa',

		#These ones are probably just typos... I wonder if I can just like, send a pull request or something. But then I might actually be wrong
		'BEC': 'Bec',
		'Dreamworks': 'DreamWorks',
		'Elite System': 'Elite Systems',
		'enix': 'Enix',
		'EPYX': 'Epyx',
		'GTC Inc.': 'GTC Inc',
		'Hi Tech Expressions': 'Hi-Tech Expressions',
		'Microprose': 'MicroProse',
		'Mindscapce': 'Mindscape', #Yeah okay, that _definitely_ is a typo
		'Pack-In-Video': 'Pack-In Video',
		'SpectraVideo': 'Spectravideo',
		'Take Two Interactive': 'Take-Two Interactive',
		'VAP': 'Vap',
	}.get(manufacturer, manufacturer)

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
