import re
import zlib
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any, Optional, cast
from xml.etree import ElementTree

from meowlauncher.common_types import EmulationStatus
from meowlauncher.config.main_config import main_config
from meowlauncher.metadata import Date, Metadata

from .mame_helpers import get_image, verify_software_list
from .mame_support_files import add_history
from .mame_utils import consistentify_manufacturer, image_config_keys

SoftwareCustomMatcher = Callable[..., bool] #Actually the first argument is SoftwarePart and then variable arguments after that, which I can't specify right now… maybe that's a sign I'm doing it wrong

is_release_date_with_thing_at_end = re.compile(r'\d{8}\s\(\w+\)')
def parse_release_date(release_info: str) -> Optional[Date]:
	if is_release_date_with_thing_at_end.match(release_info):
		release_info = release_info[:8]

	if len(release_info) != 8:
		return None

	year = release_info[0:4]
	month = release_info[4:6]
	day = release_info[6:8]
	
	return Date(year=None if year == 'xxxx' else year, month=None if month == 'xx' else month, day=None if day == 'xx' else day, is_guessed='x' in release_info or '?' in release_info)

def format_crc32_for_software_list(crc: int) -> str:
	return '{:08x}'.format(crc)

def get_crc32_for_software_list(data: bytes) -> str:
	return format_crc32_for_software_list(zlib.crc32(data) & 0xffffffff)

split_preserve_brackets = re.compile(r', (?![^(]*\))')
ends_with_brackets = re.compile(r'([^()]+)\s\(([^()]+)\)$')
def add_alt_titles(metadata: Metadata, alt_title: str):
	#Argh this is annoying because we don't want to split in the middle of brackets
	for piece in split_preserve_brackets.split(alt_title):
		ends_with_brackets_match = ends_with_brackets.match(piece)
		if ends_with_brackets_match:
			name_type = ends_with_brackets_match[2]
			if name_type in {'Box', 'USA Box', 'US Box', 'French Box', 'Box?', 'Cart', 'cart', 'Label', 'label', 'Fra Box'}:
				#There must be a better way for me to do this…
				metadata.add_alternate_name(ends_with_brackets_match[1], name_type.title().replace(' ', '-').replace('?', '') + '-Title')
			elif name_type in {'Box, Cart', 'Box/Card'}:
				#Grr
				metadata.add_alternate_name(ends_with_brackets_match[1], 'Box Title')
				metadata.add_alternate_name(ends_with_brackets_match[1], 'Cart Title')
			elif name_type == 'Japan':
				metadata.add_alternate_name(ends_with_brackets_match[1], 'Japanese Name')
			elif name_type == 'China':
				metadata.add_alternate_name(ends_with_brackets_match[1], 'Chinese Name')
			else:
				#Sometimes the brackets are actually part of the name
				metadata.add_alternate_name(piece, name_type)
		else:
			metadata.add_alternate_name(piece)

def parse_size_attribute(attrib: Optional[str]) -> Optional[int]:
	if not attrib:
		return None
	return int(attrib, 16 if attrib.startswith('0x') else 10)

class DataAreaROM():
	def __init__(self, xml: ElementTree.Element, data_area: 'DataArea'):
		self.xml = xml
		self.data_area = data_area
	#Other properties as defined in DTD: length (what's the difference with size?), loadflag (probably not needed for our purposes)

	@property
	def name(self) -> Optional[str]:
		return self.xml.attrib.get('name')

	@property
	def size(self) -> int:
		return parse_size_attribute(self.xml.attrib.get('size')) or 0

	@property
	def status(self) -> str:
		return self.xml.attrib.get('status', 'good')

	@property
	def crc32(self) -> Optional[str]:
		return self.xml.attrib.get('crc')
	
	@property
	def sha1(self) -> Optional[str]:
		return self.xml.attrib.get('sha1')

	@property
	def offset(self) -> int:
		return parse_size_attribute(self.xml.attrib.get('offset')) or 0

	def matches(self, crc32: Optional[str], sha1: Optional[str]) -> bool:
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
		self.roms = {DataAreaROM(rom_xml, self) for rom_xml in self.xml.iterfind('rom')}

	@property
	def size(self) -> Optional[int]:
		return parse_size_attribute(self.xml.attrib.get('size', '0'))

	@property
	def romless(self) -> bool:
		#name = nodata?
		return not self.roms

	@property
	def not_dumped(self) -> bool:
		#This will come up as being "best available" with -verifysoftlist/-verifysoftware, but would be effectively useless (if you tried to actually load it as software it would go boom because file not found)
		return all(rom.status == 'nodump' for rom in self.roms) if self.roms else False

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
				chunk_crc32 = get_crc32_for_software_list(chunk)
				if rom_segment.crc32 != chunk_crc32:
					return False

			return True
		return False

class DiskAreaDisk():
	def __init__(self, xml: ElementTree.Element, disk_area: 'DiskArea'):
		self.xml = xml
		self.disk_area = disk_area

	@property
	def name(self) -> Optional[str]:
		return self.xml.attrib.get('name')

	@property
	def sha1(self) -> Optional[str]:
		return self.xml.attrib.get('sha1')

	@property
	def writeable(self) -> bool:
		return self.xml.attrib.get('writeable', 'no') == 'yes'
	
	@property
	def status(self) -> str:
		return self.xml.attrib.get('status', 'good')

class DiskArea():
	def __init__(self, xml: ElementTree.Element, part: 'SoftwarePart'):
		self.xml = xml
		self.part = part
		self.disks = {DiskAreaDisk(disk_xml, self) for disk_xml in self.xml.iterfind('disk')}

	@property
	def name(self) -> Optional[str]:
		return self.xml.attrib.get('name')
	#No size attribute

	@property
	def not_dumped(self) -> bool:
		#This will come up as being "best available" with -verifysoftlist/-verifysoftware, but would be effectively useless (if you tried to actually load it as software it would go boom because file not found)
		return all(rom.status == 'nodump' for rom in self.disks) if self.disks else False

class SoftwarePart():
	def __init__(self, xml: ElementTree.Element, software: 'Software'):
		self.xml = xml
		self.software = software
		#TODO: Proper nested comprehension
		self.data_areas = {data_area.name: data_area for data_area in tuple(DataArea(data_area_xml, self) for data_area_xml in self.xml.iterfind('dataarea'))}
		self.disk_areas = {disk_area.name: disk_area for disk_area in tuple(DiskArea(disk_area_xml, self) for disk_area_xml in self.xml.iterfind('diskarea'))}

	@property
	def name(self) -> Optional[str]:
		return self.xml.attrib.get('name')

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

	def get_feature(self, name) -> Optional[str]:
		for feature in self.xml.iterfind('feature'):
			if feature.attrib.get('name') == name:
				return feature.attrib.get('value')

		return None

	@property
	def interface(self) -> Optional[str]:
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
				sha1_lower = args.sha1.lower()
				for disk_area in self.disk_areas.values():
					for disk in disk_area.disks:
						if not disk.sha1:
							continue
						if disk.sha1.lower() == sha1_lower:
							return True
			return False

		return data_area.matches(args)

	def has_data_area(self, name: str) -> bool:
		#Should probably use name in self.data_areas directly
		return name in self.data_areas

class Software():
	def __init__(self, xml: ElementTree.Element, software_list: 'SoftwareList'):
		self.xml = xml
		self.software_list = software_list

		#TODO: Proper nested comprehension
		self.parts = {part.name: part for part in tuple(SoftwarePart(part_xml, self) for part_xml in self.xml.iterfind('part'))}
		self.infos = {info.attrib.get('name', ''): info.attrib.get('value') for info in self.xml.iterfind('info')} #Blank info name should not happen

	@property
	def name(self) -> Optional[str]:
		return self.xml.attrib.get('name')
	
	@property
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
		#This will come up as being "best available" with -verifysoftlist/-verifysoftware, but would be effectively useless (if you tried to actually load it as software it would go boom because file not found)
		#Not actually sure what happens in this scenario with multiple parts, or somehow no parts
		return all(part.not_dumped for part in self.parts.values())

	def get_part(self, name: Optional[str]=None) -> SoftwarePart:
		if name:
			return self.parts[name]
		first_part = self.xml.find('part')
		if not first_part:
			raise KeyError('nope') #Should this even happen?
		return SoftwarePart(first_part, self)

	def get_info(self, name: str) -> Optional[str]:
		#Don't need this anymore, really
		return self.infos.get(name)

	def get_shared_feature(self, name: str) -> Optional[str]:
		for info in self.xml.iterfind('sharedfeat'):
			if info.attrib.get('name') == name:
				return info.attrib.get('value')

		return None

	def get_part_feature(self, name: str) -> Optional[str]:
		#Hmm
		return self.get_part().get_feature(name)

	def has_data_area(self, name: str) -> bool:
		#Hmm is this function really useful to have around
		#Is part.has_data_area really that useful?
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
	def compatibility(self) -> Optional[Sequence[str]]:
		compat = self.get_shared_feature('compatibility')
		if not compat:
			return None
		return compat.split(',')

	@property
	def parent_name(self) -> Optional[str]:
		return self.xml.attrib.get('cloneof')

	@property
	def serial(self) -> Optional[str]:
		return self.infos.get('serial')

	def add_standard_metadata(self, metadata: Metadata):
		metadata.specific_info['MAME Software Name'] = self.name
		metadata.specific_info['MAME Software Full Name'] = self.description
		#We'll need to use that as more than just a name, though, I think; and by that I mean I get dizzy if I think about whether I need to do that or not right now
		metadata.add_alternate_name(self.description, 'Software List Name')

		cloneof = self.xml.attrib.get('cloneof')
		if cloneof:
			metadata.specific_info['MAME Software Parent'] = cloneof

		metadata.specific_info['MAME Software List Name'] = self.software_list.name
		metadata.specific_info['MAME Software List Description'] = self.software_list.description

		serial = self.serial
		if serial:
			metadata.product_code = serial
		barcode = self.infos.get('barcode')
		if barcode:
			metadata.specific_info['Barcode'] = barcode
		ring_code = self.infos.get('ring_code')
		if ring_code:
			metadata.specific_info['Ring Code'] = ring_code
		
		version = self.infos.get('version')
		if version:
			if version[0].isdigit():
				version = 'v' + version
			metadata.specific_info['Version'] = version

		alt_title = self.infos.get('alt_title', self.infos.get('alt_name', self.infos.get('alt_disk')))
		if alt_title:
			add_alt_titles(metadata, alt_title)

		year_text = self.xml.findtext('year')
		if year_text:
			year_guessed = False
			if len(year_text) == 5 and year_text[-1] == '?':
				#Guess I've created a year 10000 problem, please fix this code in several millennia to be more smart
				year_guessed = True
				year_text = year_text[:-1]
			year = Date(year_text, is_guessed=year_guessed)
			if year.is_better_than(metadata.release_date):
				metadata.release_date = year

		release = self.infos.get('release')
		release_date: Optional[Date] = None
		if release:
			release_date = parse_release_date(release)

		if release_date:
			if release_date.is_better_than(metadata.release_date):
				metadata.release_date = release_date

		metadata.specific_info['MAME Emulation Status'] = self.emulation_status
		developer = consistentify_manufacturer(self.infos.get('developer'))
		if not developer:
			developer = consistentify_manufacturer(self.infos.get('author'))
		if not developer:
			developer = consistentify_manufacturer(self.infos.get('programmer'))
		if developer:
			metadata.developer = developer

		publisher = consistentify_manufacturer(self.xml.findtext('publisher'))
		if publisher:
			already_has_publisher = metadata.publisher and (not metadata.publisher.startswith('<unknown'))
			if publisher in {'<doujin>', '<homebrew>', '<unlicensed>'} and developer:
				metadata.publisher = developer
			elif not (already_has_publisher and (publisher == '<unknown>')):
				if ' / ' in publisher:
					publishers: Iterable[str] = (cast(str, consistentify_manufacturer(p)) for p in publisher.split(' / '))
					if main_config.sort_multiple_dev_names:
						publishers = sorted(publishers)
					publisher = ', '.join(publishers)

				metadata.publisher = publisher

		self.add_related_images(metadata)

		add_history(metadata, self.software_list_name, self.name)

	def add_related_images(self, metadata: Metadata):
		for image_name, config_key in image_config_keys.items():
			image = get_image(config_key, self.software_list_name, self.name)
			if image:
				metadata.images[image_name] = image
				continue
			if self.parent_name:
				image = get_image(config_key, self.software_list_name, self.parent_name)
				if image:
					metadata.images[image_name] = image


class SoftwareMatcherArgs():
	def __init__(self, crc32: Optional[str], sha1: Optional[str], size: Optional[int], reader: Optional[Callable[[int, int], bytes]]):
		self.crc32 = crc32
		self.sha1 = sha1
		self.size = size
		self.reader = reader

class SoftwareList():
	def __init__(self, path: Path) -> None:
		self.xml = ElementTree.parse(path)

	@property
	def name(self) -> str:
		return self.xml.getroot().attrib['name']

	@property
	def description(self) -> Optional[str]:
		return self.xml.getroot().attrib.get('description')

	def get_software(self, name: str) -> Optional[Software]:
		for software in self.xml.iterfind('software'):
			if software.attrib.get('name') == name:
				return Software(software, self)
		return None

	def find_all_software_with_custom_matcher(self, matcher: SoftwareCustomMatcher, args: Sequence[Any]) -> Iterable[Software]:
		for software_xml in self.xml.iterfind('software'):
			software = Software(software_xml, self)
			for part in software.parts.values():
				#There will be multiple parts sometimes, like if there's multiple floppy disks for one game (will have name = flop1, flop2, etc)
				#diskarea is used instead of dataarea seemingly for CDs or anything else that MAME would use a .chd for in its software list
				if matcher(part, *args):
					yield software

	def find_software_with_custom_matcher(self, matcher: SoftwareCustomMatcher, args: Sequence[Any]) -> Optional[Software]:
		for software_xml in self.xml.iterfind('software'):
			software = Software(software_xml, self)
			for part in software.parts.values():
				#There will be multiple parts sometimes, like if there's multiple floppy disks for one game (will have name = flop1, flop2, etc)
				#diskarea is used instead of dataarea seemingly for CDs or anything else that MAME would use a .chd for in its software list
				if matcher(part, *args):
					return software
		return None

	def find_software(self, args: SoftwareMatcherArgs) -> Optional[Software]:
		for software_xml in self.xml.iterfind('software'):
			software = Software(software_xml, self)
			for part in software.parts.values():
				#There will be multiple parts sometimes, like if there's multiple floppy disks for one game (will have name = flop1, flop2, etc)
				#diskarea is used instead of dataarea seemingly for CDs or anything else that MAME would use a .chd for in its software list
				if part.matches(args):
					return software
		return None

	_verifysoftlist_result = None
	def get_available_software(self) -> Iterable[Software]:
		#Only call -verifysoftlist if we need to, i.e. don't if it's entirely a romless softlist
		
		for software_xml in self.xml.iterfind('software'):
			software = Software(software_xml, self)
			if software.romless:
				yield software
			elif software.not_dumped:
				continue
			else:
				if self._verifysoftlist_result is None:
					self._verifysoftlist_result = verify_software_list(self.name)
				if software.name in self._verifysoftlist_result:
					yield software
