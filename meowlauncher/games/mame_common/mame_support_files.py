import functools
import os
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from typing import NamedTuple, Optional

from meowlauncher.metadata import Metadata
from meowlauncher.util.region_info import (Language,
                                           get_language_by_english_name)

from .mame_helpers import default_mame_configuration


class HistoryXML():
	def __init__(self, path: str) -> None:
		self.xml = ElementTree.parse(path)
		self.system_histories: dict[str, History] = {}
		self.software_histories: dict[str, dict[str, History]] = {}
		for entry in self.xml.findall('entry'):
			text = entry.findtext('text')
			if not text:
				continue

			systems = entry.find('systems')
			if systems is not None:
				for system in systems.findall('system'):
					self.system_histories[system.attrib['name']] = parse_history(text)
			softwares = entry.find('software')
			if softwares is not None:
				for item in softwares.findall('item'):
					if item.attrib['list'] not in self.software_histories:
						self.software_histories[item.attrib['list']] = {}
					self.software_histories[item.attrib['list']][item.attrib['name']] = parse_history(text)
	
def get_default_history_xml() -> Optional[HistoryXML]:
	if not default_mame_configuration:
		return None
	dat_paths = default_mame_configuration.ui_config.get('historypath')
	if not dat_paths:
		return None
	for dat_path in dat_paths:
		historypath = os.path.join(dat_path, 'history.xml')		
		try:
			return HistoryXML(historypath)
		except FileNotFoundError:
			continue
	return None

class History(NamedTuple):
	description: Optional[str]
	cast: Optional[str]
	technical_info: Optional[str]
	trivia: Optional[str]
	tips_and_tricks: Optional[str]
	updates: Optional[str]
	scoring: Optional[str]
	series: Optional[str]
	staff: Optional[str]
	ports: Optional[str]

def parse_history(history: str) -> History:
	lines = [line.strip() for line in history.strip().splitlines()]
	description_start = 0
	if '(c)' in lines[0]:
		description_start = 2
	if '(c)' in lines[2]:
		description_start = 4

	cast_start = None
	technical_start = None
	trivia_start = None
	updates_start = None
	scoring_start = None
	tips_and_tricks_start = None
	series_start = None
	staff_start = None
	ports_start = None
	end_line = len(lines) - 1
	for i, line in enumerate(lines):
		if line in ('- CAST OF CHARACTERS -', '- CAST OF ELEMENTS -'):
			#I think they are the same thing but only one will appear
			cast_start = i
		elif line == '- TECHNICAL -':
			technical_start = i
		elif line == '- TRIVIA -':
			trivia_start = i
		elif line == '- UPDATES -':
			updates_start = i
		elif line == '- SCORING -':
			scoring_start = i
		elif line == '- TIPS AND TRICKS -':
			tips_and_tricks_start = i
		elif line == '- SERIES -':
			series_start = i
		elif line == '- STAFF -':
			staff_start = i
		elif line == '- PORTS -':
			ports_start = i
		elif line == '- CONTRIBUTE -':
			end_line = i #We don't care about things after this
		#elif len(line) > 4 and line.startswith('-') and line.endswith('-') and line[2:-2].isupper():
		#	print('Hmm', machine_or_softlist, software_name, 'has a new section', line)
	
	#sections = [description_start, cast_start, technical_start, trivia_start, updates_start, scoring_start, tips_and_tricks_start, series_start, staff_start, ports_start, end_line]
	section_starts = (
		('description', description_start),
		('cast', cast_start),
		('technical_info', technical_start),
		('trivia', trivia_start),
		('updates', updates_start),
		('scoring', scoring_start),
		('tips_and_tricks', tips_and_tricks_start),
		('series', series_start),
		('staff', staff_start),
		('ports', ports_start),
		('<end>', end_line),
	)

	#description_end = next(section for section in sections[1:] if section)
	description_end = next(section[1] for section in section_starts[1:] if section[1]) or end_line

	sections: dict[str, Optional[str]] = {}
	for i, name_and_start in enumerate(section_starts):
		name, start = name_and_start
		if i == 0:
			if description_end - 1 > description_start:
				sections[name] = '\n'.join(lines[description_start: description_end])
			else:
				sections[name] = None
		elif i < (len(section_starts) - 1):
			if start:
				end = next(section[1] for section in section_starts[i + 1:] if section[1])
				sections[name] = '\n'.join(lines[start + 1: end])
			else:
				sections[name] = None
	return History(**sections)

def add_history(metadata: Metadata, machine_or_softlist: str, software_name: Optional[str]=None, history_xml: Optional[HistoryXML]=None) -> None:
	if not history_xml:
		if not hasattr(add_history, 'default_history_xml'):
			add_history.default_history_xml = get_default_history_xml() #type: ignore[attr-defined]
		history_xml = add_history.default_history_xml #type: ignore[attr-defined]
		if not history_xml:
			raise ValueError('Need to specify history_xml if there is no ui.ini/historypath/history.xml')

	if software_name:
		softlist = history_xml.software_histories.get(machine_or_softlist)
		if not softlist:
			return
		history = softlist.get(software_name)
	else:
		history = history_xml.system_histories.get(machine_or_softlist)

	if not history:
		return
	
	if history.description:
		if 'Description' in metadata.descriptions:
			metadata.descriptions['History-Description'] = history.description
		else:
			metadata.descriptions['Description'] = history.description

	if history.technical_info:
	 	metadata.descriptions['Technical'] = history.technical_info
	if history.trivia:
	 	metadata.descriptions['Trivia'] = history.trivia
	if history.tips_and_tricks:
	 	metadata.descriptions['Tips-And-Tricks'] = history.tips_and_tricks
	if history.updates:
	 	metadata.descriptions['Updates'] = history.updates

def get_default_mame_categories_folders() -> list[str]:
	if not default_mame_configuration:
		return []
	ui_config = default_mame_configuration.ui_config
	return ui_config.get('categorypath', [])

def _parse_mame_cat_ini(path: str) -> dict[str, list[str]]:
	with open(path, 'rt') as f:
		d: dict[str, list[str]] = {}
		current_section = None
		for line in f:
			line = line.strip()
			#Don't need to worry about FOLDER_SETTINGS or ROOT_FOLDER sections though I guess this code is gonna put them in there
			if line.startswith(';'):
				continue
			if line.startswith('['):
				current_section = line[1:-1]
			elif current_section:
				if current_section not in d:
					d[current_section] = []
				d[current_section].append(line)
		return d

#TODO: This should be able to take category_folders: Optional[Iterable[str]]=None parameter but that's not hashable, see how much functools.cache matters
@functools.cache
def get_mame_folder(name: str) -> dict[str, list[str]]:
	#if not category_folders:
	category_folders = get_default_mame_categories_folders()
	if not category_folders:
		return {}

	for folder in category_folders:
		cat_path = os.path.join(folder, name + '.ini')
		try:
			return _parse_mame_cat_ini(cat_path)						
		except FileNotFoundError:
			continue
	return {}

@functools.cache
def get_machine_folder(basename: str, folder_name: str) -> Optional[list[str]]:
	folder = get_mame_folder(folder_name)
	if not folder:
		return None
	return [section for section, names in folder.items() if basename in names]

@dataclass
class MachineCategory():
	genre: str
	subgenre: str
	
	@property
	def is_arcade(self) -> bool:
		return False
	
	@property
	def is_pinball(self) -> bool:
		#There are a few things under Arcade: Electromechanical / Utilities that are also pinball stuff, although perhaps not all of them. It only becomes apparent due to them using the "genpin" sample set
		return self.genre == 'Electromechanical' and self.subgenre == 'Pinball'

	@property
	def is_handheld_game(self) -> bool:
		#Note: "Handheld / Electronic Game" could also be a tabletop system which takes AC input and you would not be able to hold in your hands at all (e.g.: cpacman), but since catlist.ini doesn't take that into account, I don't really have a way of doing so either
		return self.genre == 'Handheld' and self.subgenre == 'Electronic Game'

	@property
	def is_gambling(self) -> bool:
		return self.is_arcade and ((self.genre == 'Casino') or (self.genre == 'Slot Machine') or (self.genre == 'Electromechanical' and self.subgenre == 'Reels') or (self.genre == 'Multiplay' and self.subgenre == 'Cards'))

	@property
	def is_plug_and_play(self) -> bool:
		return (self.genre == 'Game Console' and self.subgenre in ('Home Videogame', 'MultiGames')) or \
			(self.subgenre == 'Handheld' and (self.subgenre.startswith("Plug n' Play TV Game") or self.subgenre == 'Console Cartridge'))

	@property
	def is_coin_pusher(self) -> bool:
		return (self.genre == 'Misc.' and self.subgenre == 'Coin Pusher') or (self.genre == 'Coin Pusher' and self.subgenre == 'Misc.')

class ArcadeCategory(MachineCategory):
	def __init__(self, main_category: str, genre: str, subgenre: str, is_mature: bool) -> None:
		super().__init__(genre, subgenre)
		self.main_category = main_category
		self.is_mature = is_mature

	@property
	def is_arcade(self) -> bool:
		return self.main_category == 'Arcade'

	@property
	def is_plug_and_play(self) -> bool:
		return False

@dataclass
class OrganizedCatlist():
	platform: Optional[str]
	genre: Optional[str]
	subgenre: Optional[str]
	category: Optional[str]
	definite_platform: bool
	definite_category: bool

def get_category(basename: str) -> Optional[MachineCategory]:
	cats = get_machine_folder(basename, 'catlist')
	#It would theoretically be possible for a machine to appear twice, but catlist doesn't do that I think, so we should just grab the first
	if not cats:
		return None
	cat = cats[0]

	if ': ' in cat:
		category, _, genres = cat.partition(': ')
		genre, _, subgenre = genres.partition(' / ')
		is_mature = False
		if subgenre.endswith('* Mature *'):
			is_mature = True
			subgenre = subgenre.removesuffix('* Mature *')
		genre.removeprefix('TTL * ')
		
		return ArcadeCategory(category, genre, subgenre, is_mature)

	genre, _, subgenre = cat.partition(' / ')
	return MachineCategory(genre, subgenre)

def organize_catlist(catlist: MachineCategory) -> OrganizedCatlist:
	platform = None
	if isinstance(catlist, ArcadeCategory):
		platform = catlist.main_category
	genre: Optional[str] = catlist.genre
	subgenre: Optional[str] = catlist.subgenre
	category = None
	definite_platform = True
	definite_category = False
	
	#Fix some errata present in the default catlist.ini, maybe one day I should tell them about it, but I'm shy or maybe they're meant to be like that
	if subgenre == 'Laser Disk Simulator':
		#Both of these spellings appear twice...
		subgenre = 'Laserdisc Simulator'
	if subgenre == 'Punched Car':
		subgenre = 'Punched Card'
	#ddrstraw is Rhythm / Dance but it's more accurately a plug & play game, although that is the genre, so it's not wrong
	#kuzmich is just Platform / Run Jump, it's an arcade machine though (but it kinda doesn't have coins at this point in time, and I dunno if it's supposed to, or it just be like that)
	#evio is Music / Instruments which is the genre, yes, but it is indeed plug & play. Hmm...
	if catlist.is_plug_and_play:
		platform = 'Plug & Play'
		category = 'Games'
		if catlist.genre == 'Game Console' and catlist.subgenre == 'Home Videogame':
			definite_platform = False #May be actually just a game console
	if catlist.is_pinball:
		platform = 'Pinball'
	if catlist.is_handheld_game:
		platform = 'Handheld'
		category = 'Games'
	if catlist.genre == 'Handheld' and catlist.subgenre == 'Home Videogame Console':
		#Home Videogame Console seems to be used for stuff that would be normally excluded due to having software lists and hence being a platform for other software (e.g. GBA), or stuff that ends up there because it has no software list yet (e.g. Gizmondo, Sony PocketStation), but also some stuff like kcontra (Contra handheld) that should definitely be called a handheld, or various "plug & play" (except without the plug) stuff like BittBoy 300 in 1 or VG Pocket
		#Anyway that's why I put that there
		#Other category.genres of handheld: Pocket Device - Pad - PDA; Child Computer (e.g. Speak & Spell) but those seem more suited to Standalone System particularly the former
		platform = 'Handheld'
		definite_platform = False
	if catlist.genre == 'Misc.' and catlist.subgenre in ('Electronic Game', 'Electronic Board Game'):
		#"Electronic Game" could also be considered Handheld
		platform = 'Board Game'
		category = 'Games'

	if catlist.genre == 'Utilities' and catlist.subgenre == 'Update':
		definite_category = True
		category = 'Applications'
	
	if catlist.genre == 'Misc.' and catlist.subgenre == 'Unknown':
		genre = None
		subgenre = None

	if not isinstance(catlist, ArcadeCategory):
		if (catlist.genre == 'Rhythm' and catlist.subgenre == 'Dance') or (catlist.genre == 'MultiGame' and catlist.subgenre == 'Compilation') or (catlist.genre == 'Game Console' and catlist.subgenre == 'Fitness Game') or (catlist.genre == 'Music' and catlist.subgenre == 'Instruments'):
		#MultiGame / Compilation is also used for some handheld systems (and also there is Arcade: MultiGame / Compilation)
			platform = 'Plug & Play'
			category = 'Games'

	if (catlist.is_arcade and (catlist.genre == 'Misc.' and catlist.subgenre in ('Laserdisc Simulator', 'Print Club', 'Redemption'))) or (catlist.genre == 'Music' and catlist.subgenre in ('Jukebox', 'JukeBox')):
		definite_category = True
		category = catlist.subgenre

	if catlist.genre == 'Utilities' and catlist.subgenre in ('Test ROM', 'Test'):
		definite_category = True
		category = 'Tests'

	if catlist.genre == 'Electromechanical' or (catlist.is_arcade and catlist.genre in ('Medal Game', 'Utilities')):
		definite_category = True
		category = catlist.genre
		genre = catlist.subgenre
		subgenre = None

	if catlist.is_coin_pusher:
		definite_category = True
		category = 'Coin Pusher'

	if catlist.is_gambling:
		definite_category = True
		category = 'Gambling'

	if catlist.subgenre.startswith("Plug n' Play TV Game /"):
		#Oh hey we can actually have a genre now
		genre = catlist.subgenre.split(' / ')[-1]
		subgenre = None

	return OrganizedCatlist(platform, genre, subgenre, category, definite_platform, definite_category)

def get_languages(basename: str) -> Optional[list[Language]]:
	langs = get_machine_folder(basename, 'languages')
	if not langs:
		return None

	return [get_language_by_english_name(lang) for lang in langs]
