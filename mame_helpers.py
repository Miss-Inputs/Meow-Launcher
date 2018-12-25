import subprocess
import xml.etree.ElementTree as ElementTree
import re
import os
import copy

from metadata import CPUInfo, ScreenInfo
from config import cache_dir
from common import junk_suffixes

def consistentify_manufacturer(manufacturer):
	if not manufacturer:
		return None
	#Sometimes, MAME uses two different variations on what is the same exact company. Or formats the name in a way that nobody else does anywhere else.
	#I'm not going to count regional branches of a company, though. Just kinda feel like I should leave that stuff untouched.
	#Sometimes I don't know which out of the two variations is what I should go with... I just want only one of them. If any people out there are experts on the field of company names, then by all means tell me off.
	#If only there was some consistent guidelines to follow in this, and nintendo_common/sega_common/wonderswan etc...

	#Anyway. Some of these are bit... contentious? Is that the right word? Like, some of these are definitely different ways of spelling the same company and that's definitely a valid thing to deal with, but then some of these might well just be different brands used by the same company, because companies are weird like that. So at some point I'll probably need to clean this up. Hmm...
	#Yeah let's make this a big TODO to verify what formatting companies actually use themselves

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
	manufacturer = junk_suffixes.sub('', manufacturer)

	return {
		'20th Century Fox Video Games': '20th Century Fox',
		'Absolute': 'Absolute Entertainment',
		'Acclaim Entertainment': 'Acclaim',
		'Alpha Denshi Co.': 'ADK', #Renamed in 1993, but let's not make this confusing
		'American Softworks Company': 'American Softworks',
		'ASCII Entertainment': 'ASCII',
		'Atarisoft': 'Atari', #Atarisoft is just a brand name and not an actual company, so I guess I'll do this
		'Bally Gaming Co.': 'Bally',
		'BPS': 'Bullet-Proof Software', #I hope nobody else uses that acronym
		'Brøderbund Software': 'Brøderbund',
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
		'Microprose Games': 'MicroProse',
		'NEC Home Electronics': 'NEC',
		'Nihon Telenet': 'Telenet', #I guess
		'Nihon Bussan': 'Nichibutsu', #C'mon, use their preferred name
		'Ocean Software': 'Ocean',
		'Omage Micott': 'Omega Micott', #I have a feeling I'm the one who's wrong here. Never did quality check the Wonderswan licensees
		'Omori Electric': 'Omori',
		'Palm Inc': 'Palm',
		'Playmates Interactive': 'Playmates',
		'PonyCa': 'Pony Canyon',
		'ProSoft': 'Prosoft',
		'Sammy Entertainment': 'Sammy',
		'Seta Corporation': 'Seta',
		'Sierra Entertainment': 'Sierra',
		'Sierra On-Line': 'Sierra',
		'Sigma Enterprises': 'Sigma', #Every time I see this line I keep thinking "sigma balls", just thought you should know
		'Software Toolworks': 'The Software Toolworks', #It doesn't seem right that the "correct" one is the latter, but it's used more often, so I guess it is
		'Spinnaker Software': 'Spinnaker',
		'Spinnaker Software Corp': 'Spinnaker',
		'Square': 'Squaresoft', #Which is the frickin' right one?
		'Sunrise Software': 'Sunrise',
		'Taito Corporation': 'Taito',
		'Taito Corporation Japan': 'Taito',
		'Taito America Corporation': 'Taito America',
		'Team 17': 'Team17',
		'TecMagik Entertainment': 'TecMagik',
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
		'HOT・B': 'Hot-B',
		'アートディンク (Artdink)': 'Artdink',
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
		'ブローダーバンドジャパン (Brøderbund Japan)': 'Brøderbund Japan',
		'ホームデータ (Home Data)': 'Home Data',
		'ポニカ (Pony Canyon)': 'Pony Canyon',
		'ポニカ (PonyCa)': 'Pony Canyon',
		'マイクロネット (Micronet)': 'Micronet',
		'マカダミアソフト (Macadamia Soft)': 'Macadamia Soft',
		'工画堂スタジオ (Kogado Studio)': 'Kogado Studio',
		'日本ソフトバンク (Nihon SoftBank)': 'Nihon SoftBank',
		'日本テレネット (Nihon Telenet)': 'Telenet',
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
		'Hi Tech Expressions': 'Hi-Tech Expressions',
		'Jungle\'s Soft / Ultimate Products (HK)': 'Jungle Soft / Ultimate Products (HK)',
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
	raise FileNotFoundError(path)

def get_mame_ui_config():
	path = os.path.expanduser('~/.mame/ui.ini')
	if os.path.isfile(path):
		return MameConfigFile(path)
	raise FileNotFoundError(path)

class MachineNotFoundException(Exception):
	#This shouldn't be thrown unless I'm an idiot, but that may well happen
	pass

class MAMENotInstalledException(Exception):
	#This should always end up being caught, because I shouldn't assume the user has stuff installed
	pass

class MameState():
	class __MameState():
		def __init__(self):
			self.version = self.get_version()
			self.mame_xml_path = os.path.join(cache_dir, self.version) + '.xml' if self.have_mame else None
			self._have_checked_mame_xml = False

		@property
		def have_mame(self):
			return self.version is not None

		@staticmethod
		def get_version():
			try:
				version_proc = subprocess.run(['mame', '-help'], stdout=subprocess.PIPE, universal_newlines=True, check=True)
			except FileNotFoundError:
				#Should happen if and only if MAME isn't installed
				return None

			return version_proc.stdout.splitlines()[0]

		def _check_mame_xml_cache(self):
			if not self.have_mame:
				return
			if not os.path.isfile(self.mame_xml_path):
				print('New MAME version found:', self.version, ';creating XML; this may take a while (maybe like a minute or so)')
				os.makedirs(os.path.dirname(self.mame_xml_path), exist_ok=True)
				with open(self.mame_xml_path, 'wb') as f:
					subprocess.run(['mame', '-listxml'], stdout=f, stderr=subprocess.DEVNULL)
					#TODO check return code I guess (although in what ways would it fail?)
				print('Finished creating XML')

		def iter_mame_entire_xml(self):
			if not self.have_mame:
				raise MAMENotInstalledException()

			if not self._have_checked_mame_xml:
				#Should only check once
				self._check_mame_xml_cache()
				self._have_checked_mame_xml = True

			for _, element in ElementTree.iterparse(self.mame_xml_path):
				if element.tag == 'machine':
					yield element.attrib['name'], copy.copy(element)
					element.clear()

		def get_mame_xml(self, driver):
			if not self.have_mame:
				raise MAMENotInstalledException()

			try:
				proc = subprocess.run(['mame', '-listxml', driver], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
			except subprocess.CalledProcessError:
				raise MachineNotFoundException(driver)

			return ElementTree.fromstring(proc.stdout).find('machine')

	__instance = None

	@staticmethod
	def getMameState():
		if MameState.__instance is None:
			MameState.__instance = MameState.__MameState()
		return MameState.__instance

mame_state = MameState.getMameState()

def have_mame():
	return mame_state.have_mame

def iter_mame_entire_xml():
	yield from mame_state.iter_mame_entire_xml()

def get_mame_xml(driver):
	return mame_state.get_mame_xml(driver)

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

def lookup_system_cpu(driver_name):
	machine = mame_state.get_mame_xml(driver_name)
	#Guess I'll pass the potential MAMENotInstalledException to caller

	main_cpu = find_main_cpu(machine)
	if main_cpu is not None:
		cpu_info = CPUInfo()
		cpu_info.load_from_xml(main_cpu)

		return cpu_info

	return None

def lookup_system_displays(driver_name):
	machine = mame_state.get_mame_xml(driver_name)

	displays = machine.findall('display')
	screen_info = ScreenInfo()
	screen_info.load_from_xml_list(displays)
	return screen_info
