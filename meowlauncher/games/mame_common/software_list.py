import itertools
import logging
import re
import zlib
from collections.abc import Callable, Collection, Iterable, Iterator, Sequence
from dataclasses import dataclass
from enum import Enum
from functools import cache, cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from xml.etree import ElementTree

from meowlauncher.common_types import EmulationStatus
from meowlauncher.config.main_config import main_config
from meowlauncher.info import Date, GameInfo
from meowlauncher.util.name_utils import normalize_name
from meowlauncher.util.utils import find_filename_tags_at_end, find_tags

from .mame_helpers import default_mame_configuration, get_image
from .mame_support_files import add_history
from .mame_types import ROMStatus
from .mame_utils import consistentify_manufacturer, image_config_keys

if TYPE_CHECKING:
	from .mame_executable import MAMEExecutable


SoftwareCustomMatcher = Callable[..., bool] #Actually the first argument is SoftwarePart and then variable arguments after that, which I can't specify right now… maybe that's a sign I'm doing it wrong

logger = logging.getLogger(__name__)

class SoftwareStatus(Enum):
	""""supported" attribute in <software> element"""
	Supported = "yes" #default/implied
	Partial = "partial"
	Unsupported = "no"

_is_release_date_with_thing_at_end = re.compile(r'\d{8}\s\(\w+\)')
def _parse_release_date(release_info: str) -> Date | None:
	if _is_release_date_with_thing_at_end.match(release_info):
		release_info = release_info[:8]

	if len(release_info) != 8:
		return None

	year = release_info[0:4]
	month = release_info[4:6]
	day = release_info[6:8]
	
	return Date(year=None if year == 'xxxx' else year, month=None if month == 'xx' else month, day=None if day == 'xx' else day, is_guessed='x' in release_info or '?' in release_info)

_split_preserve_brackets = re.compile(r', (?![^(]*\))')
_ends_with_brackets = re.compile(r'([^()]+)\s\(([^()]+)\)$')
def _add_alt_titles(game_info: GameInfo, alt_title: str) -> None:
	#Argh this is annoying because we don't want to split in the middle of brackets
	for piece in _split_preserve_brackets.split(alt_title):
		ends_with_brackets_match = _ends_with_brackets.match(piece)
		if ends_with_brackets_match:
			name_type = ends_with_brackets_match[2]
			if name_type in {'Box', 'USA Box', 'US Box', 'French Box', 'Box?', 'Cart', 'cart', 'Label', 'label', 'Fra Box'}:
				#There must be a better way for me to do this…
				game_info.add_alternate_name(ends_with_brackets_match[1], name_type.title() + ' Title')
			elif name_type in {'Box, Cart', 'Box/Card'}:
				#Grr
				game_info.add_alternate_name(ends_with_brackets_match[1], 'Box Title')
				game_info.add_alternate_name(ends_with_brackets_match[1], 'Cart Title')
			elif name_type == 'Japan':
				game_info.add_alternate_name(ends_with_brackets_match[1], 'Japanese Name')
			elif name_type == 'China':
				game_info.add_alternate_name(ends_with_brackets_match[1], 'Chinese Name')
			else:
				#Sometimes the brackets are actually part of the name
				game_info.add_alternate_name(piece, name_type)
		else:
			game_info.add_alternate_name(piece)

def _parse_size_attribute(attrib: str | None) -> int | None:
	if not attrib:
		return None
	return int(attrib, 16 if attrib.startswith('0x') else 10)

class DataAreaROM():
	def __init__(self, xml: ElementTree.Element, data_area: 'DataArea'):
		self.xml = xml
		self.data_area = data_area
	#Other properties as defined in DTD: length (what's the difference with size?), loadflag (probably not needed for our purposes)

	@property
	def name(self) -> str | None:
		return self.xml.attrib.get('name')

	@property
	def size(self) -> int:
		return _parse_size_attribute(self.xml.attrib.get('size')) or 0

	@property
	def status(self) -> ROMStatus:
		"""ROM dump status"""
		status = self.xml.attrib.get('status')
		return ROMStatus(status) if status else ROMStatus.Good

	@cached_property
	def crc32(self) -> int | None:
		crc = self.xml.attrib.get('crc')
		return int(crc, 16) if crc else None
	
	@cached_property
	def sha1(self) -> bytes | None:
		sha1 = self.xml.attrib.get('sha1')
		return bytes.fromhex(sha1) if sha1 else None

	@property
	def offset(self) -> int:
		return _parse_size_attribute(self.xml.attrib.get('offset')) or 0

	def matches(self, crc32: int | None, sha1: bytes | None) -> bool:
		if not self.sha1 and not self.crc32:
			#Dunno what to do with roms like these that just have a loadflag attribute and no content, maybe something fancy is supposed to happen
			return False
		if sha1:
			if self.sha1 == sha1:
				return True
		if crc32:
			if self.crc32 == crc32:
				return True
		return False

class DataArea():
	def __init__(self, xml: ElementTree.Element, part: 'SoftwarePart'):
		self.xml = xml
		self.part = part
		self.name = xml.attrib.get('name')
		self.roms = {DataAreaROM(rom_xml, self) for rom_xml in self.xml.iter('rom')}

	@property
	def size(self) -> int | None:
		return _parse_size_attribute(self.xml.attrib.get('size', '0'))

	@property
	def romless(self) -> bool:
		#name = nodata?
		return not self.roms

	@property
	def not_dumped(self) -> bool:
		"""This will come up as being "best available" with -verifysoftlist/-verifysoftware, but would be effectively useless (if you tried to actually load it as software it would go boom because file not found)"""
		return all(rom.status == ROMStatus.NoDump for rom in self.roms) if self.roms else False

	def matches(self, args: 'SoftwareMatcherArgs') -> bool:
		if len(self.roms) == 1:
			for first_rom in self.roms:
				if first_rom.matches(args.crc32, args.sha1):
					return True
		elif args.reader:
			if self.size != args.size:
				return False

			for rom_segment in self.roms:
				if not rom_segment.name and not rom_segment.crc32:
					continue

				offset = rom_segment.offset
				size = rom_segment.size

				try:
					chunk = args.reader(offset, size)
				except IndexError:
					return False
				chunk_crc32 = zlib.crc32(chunk)
				if rom_segment.crc32 != chunk_crc32:
					return False

			return True
		return False

class DiskAreaDisk():
	def __init__(self, xml: ElementTree.Element, disk_area: 'DiskArea'):
		self.xml = xml
		self.disk_area = disk_area

	@property
	def name(self) -> str | None:
		return self.xml.attrib.get('name')

	@cached_property
	def sha1(self) -> bytes | None:
		sha = self.xml.attrib.get('sha1')
		return bytes.fromhex(sha) if sha else None

	@property
	def writeable(self) -> bool:
		return self.xml.attrib.get('writeable', 'no') == 'yes'
	
	@property
	def status(self) -> ROMStatus:
		"""ROM dump status"""
		status = self.xml.attrib.get('status')
		return ROMStatus(status) if status else ROMStatus.Good

class DiskArea():
	def __init__(self, xml: ElementTree.Element, part: 'SoftwarePart'):
		self.xml = xml
		self.part = part
		self.disks = {DiskAreaDisk(disk_xml, self) for disk_xml in self.xml.iter('disk')}

	@property
	def name(self) -> str | None:
		return self.xml.attrib.get('name')
	#No size attribute

	@property
	def not_dumped(self) -> bool:
		"""This will come up as being "best available" with -verifysoftlist/-verifysoftware, but would be effectively useless (if you tried to actually load it as software it would go boom because file not found)"""
		return all(rom.status == ROMStatus.NoDump for rom in self.disks) if self.disks else False

class SoftwarePart():
	def __init__(self, xml: ElementTree.Element, software: 'Software'):
		self.xml = xml
		self.software = software
		self.data_areas = {data_area.name: data_area for data_area in (DataArea(data_area_xml, self) for data_area_xml in self.xml.iter('dataarea'))}
		self.disk_areas = {disk_area.name: disk_area for disk_area in (DiskArea(disk_area_xml, self) for disk_area_xml in self.xml.iter('diskarea'))}

	@cached_property
	def name(self) -> str | None:
		return self.xml.attrib.get('name')

	@property
	def is_multiple_parts(self) -> bool:
		return self.software.has_multiple_parts

	@property
	def romless(self) -> bool:
		#(just presuming here that disks can't be romless, as this sort of thing is where you have a cart that has no ROM on it but is just a glorified jumper, etc)
		return all(data_area.romless for data_area in self.data_areas.values()) and bool(self.data_areas) and not self.disk_areas

	@property
	def not_dumped(self) -> bool:
		#This will come up as being "best available" with -verifysoftlist/-verifysoftware, but would be effectively useless (if you tried to actually load it as software it would go boom because file not found)
		
		#Ugh, there's probably a better way to express this logic, but my brain doesn't work
		if self.data_areas and self.disk_areas:
			return all(data_area.not_dumped for data_area in self.data_areas.values()) and all(disk_area.not_dumped for disk_area in self.disk_areas.values())
		if self.data_areas:
			return all(data_area.not_dumped for data_area in self.data_areas.values())
		if self.disk_areas:
			return all(disk_area.not_dumped for disk_area in self.disk_areas.values())
		return False

	def get_feature(self, name: str) -> str | None:
		for feature in self.xml.iter('feature'):
			if feature.attrib.get('name') == name:
				return feature.attrib.get('value')

		return None

	@property
	def interface(self) -> str | None:
		return self.xml.attrib.get('interface')
	
	def matches(self, args: 'SoftwareMatcherArgs') -> bool:
		data_area = None
		if len(self.data_areas) > 1:
			rom_data_area = None
			for data_area in self.data_areas.values():
				#Note that data area's name attribute can be anything like "rom" or "flop" depending on the kind of media, but the element inside will always be called "rom"
				#Seems that floppies don't get split up into multiple pieces like this, though
				if data_area.name == 'rom' and data_area.roms:
					rom_data_area = data_area
					break
			if not rom_data_area:
				return False
		elif len(self.data_areas) == 1:
			data_area = next(iter(self.data_areas.values()))
		else:
			if args.sha1:
				for disk_area in self.disk_areas.values():
					for disk in disk_area.disks:
						if not disk.sha1:
							continue
						if disk.sha1 == args.sha1:
							return True
			return False

		return data_area.matches(args)

	def has_data_area(self, name: str) -> bool:
		"""Should probably use name in self.data_areas directly"""
		return name in self.data_areas

class Software():
	def __init__(self, xml: ElementTree.Element, software_list: 'SoftwareList'):
		self.xml = xml
		self.software_list = software_list

		self.parts = {part.name: part for part in (SoftwarePart(part_xml, self) for part_xml in self.xml.iter('part'))}
		self.infos = {info.attrib['name']: info.attrib.get('value') for info in self.xml.iter('info')} #Blank info name should not happen

	def __str__(self) -> str:
		return f'{self.name} ({self.description})'

	@property
	def name(self) -> str:
		return self.xml.attrib['name'] #Blank name should not happen
	
	@cached_property
	def description(self) -> str:
		return self.xml.findtext('description', '') #Blank description should not happen

	@property
	def software_list_name(self) -> str:
		return self.software_list.name

	@property
	def has_multiple_parts(self) -> bool:
		return len(self.parts) > 1

	@property
	def romless(self) -> bool:
		#Not actually sure what happens in this scenario with multiple parts, or somehow no parts
		return all(part.romless for part in self.parts.values())

	@property
	def not_dumped(self) -> bool:
		"""This will come up as being "best available" with -verifysoftlist/-verifysoftware, but would be effectively useless (if you tried to actually load it as software it would go boom because file not found)
		Not actually sure what happens in this scenario with multiple parts, or somehow no parts"""
		return all(part.not_dumped for part in self.parts.values())

	def get_part(self, name: str | None=None) -> SoftwarePart:
		"""TODO: Name should not be optional and we should get rid of get_part_feature and has_data_area from this"""
		if name:
			return self.parts[name]
		first_part = self.xml.find('part')
		if not first_part:
			raise KeyError('nope') #Should this even happen?
		return SoftwarePart(first_part, self)

	def get_info(self, name: str) -> str | None:
		"""TODO: Don't need this anymore, really"""
		return self.infos.get(name)

	def get_shared_feature(self, name: str) -> str | None:
		for info in self.xml.iter('sharedfeat'):
			if info.attrib.get('name') == name:
				return info.attrib.get('value')

		return None

	def get_part_feature(self, name: str) -> str | None:
		"""Hmm we should remove this, it doesn't make sense here"""
		return self.get_part().get_feature(name)

	def has_data_area(self, name: str) -> bool:
		"""Hmm is this function really useful to have around
		#Is part.has_data_area really that useful either?"""
		return self.get_part().has_data_area(name)

	@property
	def emulation_status(self) -> EmulationStatus:
		supported = self.xml.attrib.get('supported', 'yes')
		if supported == 'partial':
			return EmulationStatus.Imperfect
		if supported == 'no':
			return EmulationStatus.Broken

		#Supported = "yes"
		return EmulationStatus.Good

	@property
	def compatibility(self) -> 'Sequence[str] | None':
		compat = self.get_shared_feature('compatibility')
		if not compat:
			return None
		return compat.split(',')

	@property
	def parent_name(self) -> str | None:
		return self.xml.attrib.get('cloneof')

	@property
	def parent(self) -> 'Software | None':
		if not self.parent_name:
			return None
		return self.software_list.get_software(self.parent_name)

	@property
	def serial(self) -> str | None:
		return self.infos.get('serial')

	def add_standard_info(self, game_info: GameInfo) -> None:
		game_info.specific_info['MAME Software'] = self
		#We'll need to use that as more than just a name, though, I think; and by that I mean I get dizzy if I think about whether I need to do that or not right now
		#TODO: Whatever is checking metadata.names needs to just check for game.software etc manually rather than this being here, I think
		game_info.add_alternate_name(self.description, 'Software List Name')

		game_info.specific_info['MAME Software List'] = self.software_list

		if not game_info.product_code:
			game_info.product_code = self.serial
		barcode = self.infos.get('barcode')
		if barcode:
			game_info.specific_info['Barcode'] = barcode
		ring_code = self.infos.get('ring_code')
		if ring_code:
			game_info.specific_info['Ring Code'] = ring_code
		
		version = self.infos.get('version')
		if version:
			if version[0].isdigit():
				version = 'v' + version
			game_info.specific_info['Version'] = version

		alt_title = self.infos.get('alt_title', self.infos.get('alt_name', self.infos.get('alt_disk')))
		if alt_title:
			_add_alt_titles(game_info, alt_title)

		year_text = self.xml.findtext('year')
		if year_text:
			year_guessed = False
			if len(year_text) == 5 and year_text[-1] == '?':
				#Guess I've created a year 10000 problem, please fix this code in several millennia to be more smart
				year_guessed = True
				year_text = year_text[:-1]
			year = Date(year_text, is_guessed=year_guessed)
			if year.is_better_than(game_info.release_date):
				game_info.release_date = year

		release = self.infos.get('release')
		release_date: Date | None = None
		if release:
			release_date = _parse_release_date(release)

		if release_date:
			if release_date.is_better_than(game_info.release_date):
				game_info.release_date = release_date

		developer = consistentify_manufacturer(self.infos.get('developer'))
		if not developer:
			developer = consistentify_manufacturer(self.infos.get('author'))
		if not developer:
			developer = consistentify_manufacturer(self.infos.get('programmer'))
		if developer:
			game_info.developer = developer

		publisher = consistentify_manufacturer(self.xml.findtext('publisher'))
		if publisher:
			already_has_publisher = game_info.publisher and (not isinstance(game_info.publisher, str) or not game_info.publisher.startswith('<unknown'))
			if publisher in {'<doujin>', '<homebrew>', '<unlicensed>'} and developer:
				game_info.publisher = developer
			elif not (already_has_publisher and (publisher == '<unknown>')):
				if ' / ' in publisher:
					publishers: Iterable[str] = (cast(str, consistentify_manufacturer(p)) for p in publisher.split(' / '))
					if main_config.sort_multiple_dev_names:
						publishers = sorted(publishers)
					publisher = ', '.join(publishers)

				game_info.publisher = publisher

		self.add_related_images(game_info)

		try:
			add_history(game_info, self.software_list_name, self.name)
		except FileNotFoundError:
			pass

	def add_related_images(self, game_info: GameInfo) -> None:
		for image_name, config_key in image_config_keys.items():
			image = get_image(config_key, self.software_list_name, self.name)
			if image:
				game_info.images[image_name] = image
				continue
			if self.parent_name:
				image = get_image(config_key, self.software_list_name, self.parent_name)
				if image:
					game_info.images[image_name] = image


@dataclass(frozen=True)
class SoftwareMatcherArgs():
	crc32: int | None
	sha1: bytes | None
	size: int | None
	reader: 'Callable[[int, int], bytes] | None'

class SoftwareList():
	def __init__(self, path: Path) -> None:
		self.xml = ElementTree.parse(path)
		self.software = {software.name: software for software in {Software(s, self) for s in self.xml.iter('software')}}

	def __hash__(self) -> int:
		return hash(self.name)

	def __str__(self) -> str:
		return f'{self.name} ({self.description})'

	@property
	def name(self) -> str:
		return self.xml.getroot().attrib['name']

	@property
	def description(self) -> str | None:
		return self.xml.getroot().attrib.get('description')

	def get_software(self, name: str) -> Software | None:
		#for software in self.xml.iter('software'):
		#	if software.attrib.get('name') == name:
		#		return Software(software, self)
		#return None
		return self.software.get(name)

	def iter_all_parts_with_custom_matcher(self, matcher: SoftwareCustomMatcher, args: Sequence[Any]) -> Iterator[SoftwarePart]:
		# for software_xml in self.xml.iter('software'):
		# 	software = Software(software_xml, self)
		for software in self.software.values():
			yield from (part for part in software.parts.values() if matcher(part, *args))
			
	def iter_all_software_with_custom_matcher(self, matcher: SoftwareCustomMatcher, args: Sequence[Any]) -> Iterator[Software]:
		yield from (part.software for part in self.iter_all_parts_with_custom_matcher(matcher, args))

	def find_software_part_with_custom_matcher(self, matcher: SoftwareCustomMatcher, args: Sequence[Any]) -> SoftwarePart | None:
		return next(self.iter_all_parts_with_custom_matcher(matcher, args), None)

	def find_software_with_custom_matcher(self, matcher: SoftwareCustomMatcher, args: Sequence[Any]) -> Software | None:
		return next(self.iter_all_software_with_custom_matcher(matcher, args), None)
		
	def find_software_part(self, args: SoftwareMatcherArgs) -> SoftwarePart | None:
		# for software_xml in self.xml.iter('software'):
		# 	software = Software(software_xml, self)
		for software in self.software.values():
			for part in software.parts.values():
				if part.matches(args):
					return part
		return None

	def find_software(self, args: SoftwareMatcherArgs) -> Software | None:
		part = self.find_software_part(args)
		if part:
			return part.software
		return None

	_verifysoftlist_result = None
	def iter_available_software(self, mame_executable: 'MAMEExecutable') -> Iterator[Software]:
		#Only call -verifysoftlist if we need to, i.e. don't if it's entirely a romless softlist
		
		for software_xml in self.xml.iter('software'):
			software = Software(software_xml, self)
			if software.romless:
				yield software
			elif software.not_dumped:
				continue
			else:
				if self._verifysoftlist_result is None:
					self._verifysoftlist_result = mame_executable.verifysoftlist(self.name)
				if software.name in self._verifysoftlist_result:
					yield software


def iter_all_software_lists() -> Iterator[tuple[Path, SoftwareList]]:
	if not default_mame_configuration:
		return
	hashpaths = default_mame_configuration.core_config.get('hashpath')
	if not hashpaths:
		return
	generator = (Path(hash_path).iterdir() for hash_path in hashpaths)
	try:
		for hash_xml_path in itertools.chain.from_iterable(generator):
			try:
				yield hash_xml_path, SoftwareList(hash_xml_path)
			except SyntaxError: #I guess that is the error it throws?
				logger.info('%s is fuckin borked for some reason', hash_xml_path, exc_info=True)
				continue
	except FileNotFoundError:
		pass

def iter_software_lists_by_name(names: Iterable[str]) -> Iterator[SoftwareList]:
	if not default_mame_configuration:
		return
	hashpaths = default_mame_configuration.core_config.get('hashpath')
	if not hashpaths:
		return
	try:
		yield from (SoftwareList(hash_path.joinpath(f'{name}.xml')) for hash_path, name in (itertools.product((Path(hash_path) for hash_path in hashpaths), names)))
	except FileNotFoundError:
		pass

@cache
def get_software_list_by_name(name: str) -> SoftwareList | None:
	return next(iter_software_lists_by_name((name, )), None)

def find_in_software_lists_with_custom_matcher(software_lists: Collection[SoftwareList], matcher: SoftwareCustomMatcher, args: Sequence[Any]) -> Software | None:
	for software_list in software_lists:
		software = software_list.find_software_with_custom_matcher(matcher, args)
		if software:
			return software
	return None

def _does_name_fuzzy_match(part: SoftwarePart, name: str) -> bool:
	#TODO Handle annoying multiple discs
	proto_tags = {'beta', 'proto', 'sample', 'pre-release', 'prerelease'}
	demo_tags = {'demo', 'playable game preview', 'trade demo', 'taikenban'}

	software_tags: Collection[str]
	name_tags: Collection[str]
	software_name_without_brackety_bois, software_tags = find_tags(part.software.description)
	name_without_brackety_bois, name_tags = find_tags(name)
	software_normalized_name = normalize_name(software_name_without_brackety_bois)
	normalized_name = normalize_name(name_without_brackety_bois)
	name_tags = {t.lower()[1:-1] for t in name_tags}
	#Sometimes (often) these will appear as (Region, Special Version) and not (Region) (Special Version) etc, so let's dismantle them
	software_tags = ', '.join(t.lower()[1:-1] for t in software_tags).split(', ')
	
	if 'alt' in software_tags and 'alt' not in name_tags:
		return False
	if 'alt' in name_tags and 'alt' not in software_tags:
		return False
	
	if software_normalized_name != normalized_name and not normalized_name.startswith(software_normalized_name + ' - ') and not software_normalized_name.startswith(normalized_name + ' - '):
		return False

	name_is_demo = any(t == 'demo' or t.startswith('demo ') or t.endswith(' demo') for t in name_tags)
	software_is_demo = any(t in demo_tags or t.startswith('demo ') or t.endswith(' demo') for t in software_tags)
	if (name_is_demo and not software_is_demo) or (software_is_demo and not name_is_demo):
		return False
	
	name_is_prototype = any(t in proto_tags or t.startswith('prototype') for t in name_tags)
	software_is_prototype = any(t in proto_tags or t.startswith('prototype') for t in software_tags)
	if (name_is_prototype and not software_is_prototype) or (software_is_prototype and not name_is_prototype):
		return False

	return True

def find_software_by_name(software_lists: Collection[SoftwareList], name: str) -> Software | None:
	fuzzy_name_matches = set(itertools.chain.from_iterable(software_list.iter_all_software_with_custom_matcher(_does_name_fuzzy_match, [name]) for software_list in software_lists))

	if len(fuzzy_name_matches) == 1:
		#TODO: Don't do this, we still need to check the region… but only if the region needs to be checked at all, see below comment
		#Bold of you to assume I understand this code, past Megan
		#TODO: Okay I think I see what Past Megan was trying to do here… we want to first get the matches from _does_name_fuzzy_match, then we want to filter down by region _unless_ we don't have to (because regions aren't involved), and then version if needed, so this really all happens in three parts, and yeah I guess that does mean we need to collect everything in a set so we can test length == 1
		#TODO: Should be just narrowing everything down rather than building sets over and over again, this looks weird
		return fuzzy_name_matches.pop()
	if len(fuzzy_name_matches) > 1:
		name_and_region_matches: set[Software] = set()
		regions = {
			'USA': 'USA',
			'Euro': 'Europe',
			'Jpn': 'Japan',
			'Aus': 'Australia',
			'As': 'Asia',
			'Fra': 'France',
			'Ger': 'Germany',
			'Spa': 'Spain',
			'Ita': 'Italy',
			'Ned': 'Netherlands',
			'Bra': 'Brazil',
		}
		name_brackets = {t.lower()[1:-1] for t in find_filename_tags_at_end(name)}
		for match in fuzzy_name_matches:
			#Narrow down by region
			#Sometimes (often) these will appear as (Region, Special Version) and not (Region) (Special Version) etc, so let's dismantle them
			#TODO: Don't narrow down by region if we don't have to, e.g. a region is in the name but nowhere in the software name
			match_brackets = ', '.join(t.lower()[1:-1] for t in find_filename_tags_at_end(match.description)).split(', ')
			for abbrev_region, region in regions.items():				
				if (abbrev_region.lower() in match_brackets or region.lower() in match_brackets) and region.lower() in name_brackets:
					name_and_region_matches.add(match)

		if len(name_and_region_matches) == 1:
			return name_and_region_matches.pop()

		name_and_region_and_version_matches = set()
		for match in name_and_region_matches:
			match_brackets = ', '.join(t.lower()[1:-1] for t in find_filename_tags_at_end(match.description)).split(', ')

			if 'v1.1' in match_brackets:
				if 'v1.1' in name_brackets or 'reprint' in name_brackets or 'rerelease' in name_brackets or 'rev 1' in name_brackets:
					name_and_region_and_version_matches.add(match)
					break
			#TODO Should look at the rest of name_brackets or match_brackets for anything else looking like rev X or v1.X
			#TODO Consider special versions
			#Seen in the wild:  "Limited Edition", "32X", "Sega All Stars", "Amiga CD32 Special"

			if 'v1.0' in match_brackets:
				orig_version = True
				for b in name_brackets:
					if (b not in {'rev 0', 'v1.0'} and b.startswith(('rev', 'v1.'))) or b in {'reprint', 'rerelease'}:
						orig_version = False
						break
				if orig_version:
					name_and_region_and_version_matches.add(match)

			for b in name_brackets:
				if b.startswith('rev ') and b.removeprefix('rev ').isnumeric():
					if b in match_brackets or f'v1.{b.removeprefix("rev ")}' in match_brackets:
						name_and_region_and_version_matches.add(match)
		
		if len(name_and_region_and_version_matches) == 1:
			return name_and_region_and_version_matches.pop()

		if name_and_region_matches:
			logger.debug('%s matched too many: %s', name, [m.description for m in name_and_region_matches])
		
	return None

def find_in_software_lists(software_lists: Collection[SoftwareList], args: SoftwareMatcherArgs) -> Software | None:
	"""Does not handle hash collisions… should be fine in real life, though"""
	for software_list in software_lists:
		software = software_list.find_software(args)
		if software:
			return software
	return None

def matcher_args_for_bytes(data: bytes) -> SoftwareMatcherArgs:
	"""Avoids using computing sha1, as right now that would mean it wastefully reads more than it has to"""
	return SoftwareMatcherArgs(zlib.crc32(data), None, len(data), lambda offset, amount: data[offset:offset+amount])
