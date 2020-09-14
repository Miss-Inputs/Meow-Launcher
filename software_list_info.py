import calendar
import os
import re
import xml.etree.ElementTree as ElementTree
import zlib

import io_utils
from common import (find_filename_tags_at_end, normalize_name,
                    remove_filename_tags)
from common_types import EmulationStatus, MediaType
from config.main_config import main_config
from data.subtitles import subtitles
from info.system_info import systems
from mame_helpers import (consistentify_manufacturer, get_mame_core_config,
                          image_config_keys, verify_software_list, get_image)

#Ideally, every platform wants to be able to get software list info. If available, it will always be preferred over what we can extract from inside the ROMs, as it's more reliable, and avoids the problem of bootlegs/hacks with invalid/missing header data, or publisher/developers that merge and change names and whatnot.
#We currently do this by putting a block of code inside each platform_metadata helper that does the same thing. I guess I should genericize that one day. Anyway, it's not always possible.

def parse_size_attribute(attrib):
	if not attrib:
		return None
	return int(attrib, 16 if attrib.startswith('0x') else 10)

class DataAreaROM():
	def __init__(self, xml, data_area):
		self.xml = xml
		self.data_area = data_area
	#Other properties as defined in DTD: length (what's the difference with size?), loadflag (probably not needed for our purposes)

	@property
	def name(self):
		return self.xml.attrib.get('name')

	@property
	def size(self):
		return parse_size_attribute(self.xml.attrib.get('size', '0'))

	@property
	def status(self):
		return self.xml.attrib.get('status', 'good')

	@property
	def crc32(self):
		return self.xml.attrib.get('crc')
	
	@property
	def sha1(self):
		return self.xml.attrib.get('sha1')

	@property
	def offset(self):
		return parse_size_attribute(self.xml.attrib.get('offset', '0'))

	def matches(self, crc32, sha1):
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
	def __init__(self, xml, part):
		self.xml = xml
		self.part = part
		self.roms = []

		for rom_xml in self.xml.findall('rom'):
			self.roms.append(DataAreaROM(rom_xml, self))

	@property
	def name(self):
		return self.xml.attrib.get('name')

	@property
	def size(self):
		return parse_size_attribute(self.xml.attrib.get('size', '0'))

	@property
	def romless(self):
		#name = nodata?
		return not self.roms

	@property
	def not_dumped(self):
		#This will come up as being "best available" with -verifysoftlist/-verifysoftware, but would be effectively useless (if you tried to actually load it as software it would go boom because file not found)
		return all([rom.status == 'nodump' for rom in self.roms]) if self.roms else False

	def matches(self, args):
		if len(self.roms) == 1:
			roms = self.roms
			if not roms:
				#Ignore data areas such as "sram" that don't have any ROMs associated with them.
				return False
			for rom in roms:
				if rom.matches(args.crc32, args.sha1):
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
	def __init__(self, xml, disk_area):
		self.xml = xml
		self.disk_area = disk_area

	@property
	def name(self):
		return self.xml.attrib.get('name')

	@property
	def sha1(self):
		return self.xml.attrib.get('sha1')

	@property
	def writeable(self):
		return self.xml.attrib.get('writeable', 'no') == 'yes'
	
	@property
	def status(self):
		return self.xml.attrib.get('status', 'good')

class DiskArea():
	def __init__(self, xml, part):
		self.xml = xml
		self.part = part
		self.disks = []
		
		for disk_xml in self.xml.findall('disk'):
			self.disks.append(DiskAreaDisk(disk_xml, self))

	@property
	def name(self):
		return self.xml.attrib.get('name')
	#No size attribute

	@property
	def not_dumped(self):
		#This will come up as being "best available" with -verifysoftlist/-verifysoftware, but would be effectively useless (if you tried to actually load it as software it would go boom because file not found)
		return all([rom.status == 'nodump' for rom in self.disks]) if self.disks else False

class SoftwarePart():
	def __init__(self, xml, software):
		self.xml = xml
		self.software = software
		self.data_areas = {}
		self.disk_areas = {}

		for data_area_xml in self.xml.findall('dataarea'):
			data_area = DataArea(data_area_xml, self)
			self.data_areas[data_area.name] = data_area
		for disk_area_xml in self.xml.findall('diskarea'):
			disk_area = DiskArea(disk_area_xml, self)
			self.disk_areas[disk_area.name] = disk_area

	@property
	def name(self):
		return self.xml.attrib.get('name')

	@property
	def romless(self):
		#(just presuming here that disks can't be romless, as this sort of thing is where you have a cart that has no ROM on it but is just a glorified jumper, etc)
		return all([data_area.romless for data_area in self.data_areas.values()]) and self.data_areas and not self.disk_areas

	@property
	def not_dumped(self):
		#This will come up as being "best available" with -verifysoftlist/-verifysoftware, but would be effectively useless (if you tried to actually load it as software it would go boom because file not found)
		
		#Ugh, there's probably a better way to express this logic, but my brain doesn't work
		if self.data_areas and self.disk_areas:
			return all([data_area.not_dumped for data_area in self.data_areas.values()]) and all([disk_area.not_dumped for disk_area in self.disk_areas.values()])
		if self.data_areas:
			return all([data_area.not_dumped for data_area in self.data_areas.values()])
		if self.disk_areas:
			return all([disk_area.not_dumped for disk_area in self.disk_areas.values()])
		return False

	def get_feature(self, name):
		for feature in self.xml.findall('feature'):
			if feature.attrib.get('name') == name:
				return feature.attrib.get('value')

		return None

	@property
	def interface(self):
		return self.xml.attrib.get('interface')
	
	def matches(self, args):
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
					disks = disk_area.disks
					if not disks:
						#Hmm, this might not happen
						continue
					for disk in disks:
						if not disk.sha1:
							continue
						if disk.sha1.lower() == sha1_lower:
							return True
			return False

		return data_area.matches(args)

	def has_data_area(self, name):
		#Should probably use name in self.data_areas directly
		return name in self.data_areas

split_preserve_brackets = re.compile(r', (?![^(]*\))')
ends_with_brackets = re.compile(r'([^()]+)\s\(([^()]+)\)$')
def parse_alt_title(metadata, alt_title):
	#Argh this is annoying because we don't want to split in the middle of brackets
	for piece in split_preserve_brackets.split(alt_title):
		ends_with_brackets_match = ends_with_brackets.match(piece)
		if ends_with_brackets_match:
			name_type = ends_with_brackets_match[2]
			if name_type in ('Box', 'USA Box', 'US Box', 'French Box', 'Box?', 'Cart', 'cart', 'Label', 'label', 'Fra Box'):
				#There must be a better way for me to do this…
				metadata.add_alternate_name(ends_with_brackets_match[1], name_type.title().replace(' ', '-').replace('?', '') + '-Title')
			elif name_type in ('Box, Cart', 'Box/Card'):
				#Grr
				metadata.add_alternate_name(ends_with_brackets_match[1], 'Box-Title')
				metadata.add_alternate_name(ends_with_brackets_match[1], 'Cart-Title')
			elif name_type == 'Japan':
				metadata.add_alternate_name(ends_with_brackets_match[1], 'Japanese-Name')
			elif name_type == 'China':
				metadata.add_alternate_name(ends_with_brackets_match[1], 'Chinese-Name')
			else:
				#Sometimes the brackets are actually part of the name
				metadata.add_alternate_name(piece, name_type)
		else:
			metadata.add_alternate_name(piece)

class Software():
	def __init__(self, xml, software_list):
		self.xml = xml
		self.software_list = software_list

		self.parts = {}
		for part_xml in self.xml.findall('part'):
			part = SoftwarePart(part_xml, self)
			self.parts[part.name] = part

		self.infos = {}
		for info in self.xml.findall('info'):
			self.infos[info.attrib.get('name')] = info.attrib.get('value')

	@property
	def name(self):
		return self.xml.attrib.get('name')
	
	@property
	def description(self):
		return self.xml.findtext('description')

	@property
	def software_list_name(self):
		return self.software_list.name

	@property
	def has_multiple_parts(self):
		return len(self.parts) > 1

	@property
	def romless(self):
		#Not actually sure what happens in this scenario with multiple parts, or somehow no parts
		return all([part.romless for part in self.parts.values()])

	@property
	def not_dumped(self):
		#This will come up as being "best available" with -verifysoftlist/-verifysoftware, but would be effectively useless (if you tried to actually load it as software it would go boom because file not found)
		#Not actually sure what happens in this scenario with multiple parts, or somehow no parts
		return all([part.not_dumped for part in self.parts.values()])

	def get_part(self, name=None):
		if name:
			return self.parts[name]
		return SoftwarePart(self.xml.find('part'), self)

	def get_info(self, name):
		#Don't need this anymore, really
		return self.infos.get(name)

	def get_shared_feature(self, name):
		for info in self.xml.findall('sharedfeat'):
			if info.attrib.get('name') == name:
				return info.attrib.get('value')

		return None

	def get_part_feature(self, name, part_name=None):
		#Should probably use part.get_feature instead
		if not part_name:
			part = self.get_part()
		else:
			part = self.parts[part_name]
		return part.get_feature(name)

	def has_data_area(self, name, part_name=None):
		#Should use part.has_data_area instead, or arguably name in part.data_areas
		if part_name:
			part = self.parts[part_name]
		else:
			part = self.get_part()

		return part.has_data_area(name)

	@property
	def emulation_status(self):
		supported = self.xml.attrib.get('supported', 'yes')
		if supported == 'partial':
			return EmulationStatus.Imperfect
		if supported == 'no':
			return EmulationStatus.Broken

		#Supported = "yes"
		return EmulationStatus.Good

	@property
	def compatibility(self):
		compat = self.get_shared_feature('compatibility')
		if not compat:
			return compat
		return compat.split(',')

	@property
	def parent_name(self):
		return self.xml.attrib.get('cloneof')

	def add_standard_metadata(self, metadata):
		metadata.specific_info['MAME-Software-Name'] = self.name
		metadata.specific_info['MAME-Software-Full-Name'] = self.description
		#We'll need to use that as more than just a name, though, I think; and by that I mean I get dizzy if I think about whether I need to do that or not right now
		metadata.add_alternate_name(self.description, 'Software-List-Name')

		cloneof = self.xml.attrib.get('cloneof')
		if cloneof:
			metadata.specific_info['MAME-Software-Parent'] = cloneof

		metadata.specific_info['MAME-Software-List-Name'] = self.software_list.name
		metadata.specific_info['MAME-Software-List-Description'] = self.software_list.description

		serial = self.infos.get('serial')
		if serial:
			metadata.product_code = serial
		barcode = self.infos.get('barcode')
		if barcode:
			metadata.specific_info['Barcode'] = barcode
		ring_code = self.infos.get('ring_code')
		if ring_code:
			metadata.specific_info['Ring-Code'] = ring_code
		
		version = self.infos.get('version')
		if version:
			if version[0].isdigit():
				version = 'v' + version
			metadata.specific_info['Version'] = version

		alt_title = self.infos.get('alt_title', self.infos.get('alt_name', self.infos.get('alt_disk')))
		if alt_title:
			parse_alt_title(metadata, alt_title)

		year = self.xml.findtext('year')
		if metadata.year:
			already_has_valid_year = '?' not in metadata.year if isinstance(metadata.year, str) else True
		else:
			already_has_valid_year = False
		if not ('?' in year and already_has_valid_year):
			metadata.year = year
		parse_release_date(metadata, self.infos.get('release'))

		metadata.specific_info['MAME-Emulation-Status'] = self.emulation_status
		developer = consistentify_manufacturer(self.infos.get('developer'))
		if not developer:
			developer = consistentify_manufacturer(self.infos.get('author'))
		if not developer:
			developer = consistentify_manufacturer(self.infos.get('programmer'))
		if developer:
			metadata.developer = developer

		publisher = consistentify_manufacturer(self.xml.findtext('publisher'))
		already_has_publisher = metadata.publisher and (not metadata.publisher.startswith('<unknown'))
		if publisher in ('<doujin>', '<homebrew>', '<unlicensed>') and developer:
			metadata.publisher = developer
		elif not (already_has_publisher and (publisher == '<unknown>')):
			if ' / ' in publisher:
				publishers = [consistentify_manufacturer(p) for p in publisher.split(' / ')]
				if main_config.sort_multiple_dev_names:
					publishers.sort()
				publisher = ', '.join(publishers)

			metadata.publisher = publisher

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
	def __init__(self, crc32, sha1, size, reader):
		self.crc32 = crc32
		self.sha1 = sha1
		self.size = size
		self.reader = reader #(seek_to, amount) > bytes

class SoftwareList():
	def __init__(self, path):
		self.xml = ElementTree.parse(path)

	@property
	def name(self):
		return self.xml.getroot().attrib.get('name')

	@property
	def description(self):
		return self.xml.getroot().attrib.get('description')

	def get_software(self, name):
		for software in self.xml.findall('software'):
			if software.attrib.get('name') == name:
				return Software(software, self)
		return None

	def find_all_software_with_custom_matcher(self, matcher, args):
		results = []
		for software_xml in self.xml.findall('software'):
			software = Software(software_xml, self)
			for part in software.parts.values():
				#There will be multiple parts sometimes, like if there's multiple floppy disks for one game (will have name = flop1, flop2, etc)
				#diskarea is used instead of dataarea seemingly for CDs or anything else that MAME would use a .chd for in its software list
				if matcher(part, *args):
					results.append(software)
		return results

	def find_software_with_custom_matcher(self, matcher, args):
		for software_xml in self.xml.findall('software'):
			software = Software(software_xml, self)
			for part in software.parts.values():
				#There will be multiple parts sometimes, like if there's multiple floppy disks for one game (will have name = flop1, flop2, etc)
				#diskarea is used instead of dataarea seemingly for CDs or anything else that MAME would use a .chd for in its software list
				if matcher(part, *args):
					return software
		return None

	def find_software(self, args):
		for software_xml in self.xml.findall('software'):
			software = Software(software_xml, self)
			for part in software.parts.values():
				#There will be multiple parts sometimes, like if there's multiple floppy disks for one game (will have name = flop1, flop2, etc)
				#diskarea is used instead of dataarea seemingly for CDs or anything else that MAME would use a .chd for in its software list
				if part.matches(args):
					return software
		return None

	_verifysoftlist_result = None
	def get_available_software(self):
		available = []

		#Only call -verifysoftlist if we need to, i.e. don't if it's entirely a romless softlist
		
		for software_xml in self.xml.findall('software'):
			software = Software(software_xml, self)
			if software.romless:
				available.append(software)
			elif software.not_dumped:
				continue
			else:
				if self._verifysoftlist_result is None:
					self._verifysoftlist_result = verify_software_list(self.name)
				if software.name in self._verifysoftlist_result:
					available.append(software)
		
		return available

def get_software_lists_by_names(names):
	if not names:
		return []
	return [software_list for software_list in [get_software_list_by_name(name) for name in names] if software_list]

_software_list_cache = {}
def get_software_list_by_name(name):
	global _software_list_cache
	if name in _software_list_cache:
		return _software_list_cache[name]

	try:
		mame_config = get_mame_core_config()
		for hash_path in mame_config.get('hashpath', []):
			if os.path.isdir(hash_path):
				list_path = os.path.join(hash_path, name + '.xml')
				if os.path.isfile(list_path):
					software_list = SoftwareList(list_path)
					_software_list_cache[name] = software_list
					return software_list
		return None #In theory though, we shouldn't be asking for software lists that don't exist
	except FileNotFoundError:
		return None

def find_in_software_lists_with_custom_matcher(software_lists, matcher, args):
	for software_list in software_lists:
		software = software_list.find_software_with_custom_matcher(matcher, args)
		if software:
			return software
	return None

def find_software_by_name(software_lists, name):
	def _does_name_fuzzy_match(part, name):
		#TODO Handle annoying multiple discs
		proto_tags = ['beta', 'proto', 'sample']

		software_name_without_brackety_bois = remove_filename_tags(part.software.description)
		name_without_brackety_bois = remove_filename_tags(name)
		software_normalized_name = normalize_name(software_name_without_brackety_bois)
		normalized_name = normalize_name(name_without_brackety_bois)
		name_tags = [t.lower()[1:-1] for t in find_filename_tags_at_end(name)]
		#Sometimes (often) these will appear as (Region, Special Version) and not (Region) (Special Version) etc, so let's dismantle them
		software_tags = ', '.join([t.lower()[1:-1] for t in find_filename_tags_at_end(part.software.description)]).split(', ')
		
		if software_normalized_name != normalized_name:
			if name_without_brackety_bois in subtitles:
				if normalize_name(name_without_brackety_bois + ': ' + subtitles[name_without_brackety_bois]) != software_normalized_name:
					return False
			elif software_name_without_brackety_bois in subtitles:
				if normalize_name(software_name_without_brackety_bois + ': ' + subtitles[software_name_without_brackety_bois]) != normalized_name:
					return False
			else:
				return False
		if 'demo' in software_tags and 'demo' not in (', ').join(name_tags):
			return False
		if 'demo' in name_tags and 'demo' not in software_tags:
			return False

		software_is_prototype = any(t.startswith('prototype') for t in software_tags)

		for t in proto_tags:
			if t in name_tags and not (t in software_tags or software_is_prototype):
				return False
			if t in software_tags and not t in name_tags:
				return False
		if software_is_prototype:
			matches_proto = False
			for t in proto_tags:
				if t in name_tags:
					matches_proto = True
			if not matches_proto:
				return False
		return True

	fuzzy_name_matches = []
	for software_list in software_lists:
		results = software_list.find_all_software_with_custom_matcher(_does_name_fuzzy_match, [name])
		fuzzy_name_matches += results
	if len(fuzzy_name_matches) == 1:
		#TODO: Don't do this, we still need to check the region… but only if the region needs to be checked at all, see below comment
		return fuzzy_name_matches[0]
	if len(fuzzy_name_matches) > 1:
		name_and_region_matches = []
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
		name_brackets = [t.lower()[1:-1] for t in find_filename_tags_at_end(name)]
		for match in fuzzy_name_matches:
			#Narrow down by region
			#Sometimes (often) these will appear as (Region, Special Version) and not (Region) (Special Version) etc, so let's dismantle them
			#TODO: Don't narrow down by region if we don't have to, e.g. a region is in the name but nowhere in the software name
			match_brackets = ', '.join([t.lower()[1:-1] for t in find_filename_tags_at_end(match.description)]).split(', ')
			for abbrev_region, region in regions.items():				
				if (abbrev_region.lower() in match_brackets or region.lower() in match_brackets) and region.lower() in name_brackets:
					name_and_region_matches.append(match)

		if len(name_and_region_matches) == 1:
			return name_and_region_matches[0]

		name_and_region_and_version_matches = []
		for match in name_and_region_matches:
			match_brackets = ', '.join([t.lower()[1:-1] for t in find_filename_tags_at_end(match.description)]).split(', ')
			if 'v1.1' in match_brackets:
				if 'v1.1' in name_brackets or 'reprint' in name_brackets or 'rerelease' in name_brackets or 'rev 1' in name_brackets:
					name_and_region_and_version_matches.append(match)
					break
			#TODO Should look at the rest of name_brackets or match_brackets for anything else looking like rev X or v1.X
			#TODO Consider special versions
			#Seen in the wild:  "Limited Edition", "32X", "Sega All Stars", "Amiga CD32 Special"

			if 'v1.0' in match_brackets:
				orig_version = True
				for b in name_brackets:
					if (b not in ('rev 0', 'v1.0') and b.startswith(('rev', 'v1.'))) or b in ('reprint', 'rerelease'):
						orig_version = False
						break
				if orig_version:
					name_and_region_and_version_matches.append(match)
		
		if len(name_and_region_and_version_matches) == 1:
			return name_and_region_and_version_matches[0]

		#print(name, 'matched too many', [m.description for m in name_and_region_matches])
		
	return None

def find_in_software_lists(software_lists, args):
	#TODO: Handle hash collisions. Could happen, even if we're narrowing down to specific software lists
	for software_list in software_lists:
		software = software_list.find_software(args)
		if software:
			return software
	return None

class UnsupportedCHDError(Exception):
	pass

def get_sha1_from_chd(chd_path):
	header = io_utils.read_file(chd_path, amount=124)
	if header[0:8] != b'MComprHD':
		raise UnsupportedCHDError('Header magic %s unknown' % str(header[0:8]))
	chd_version = int.from_bytes(header[12:16], 'big')
	if chd_version == 4:
		sha1 = header[48:68]
	elif chd_version == 5:
		sha1 = header[84:104]
	else:
		raise UnsupportedCHDError('Version %d unknown' % chd_version)
	return bytes.hex(sha1)

def matcher_args_for_bytes(data):
	#We _could_ use sha1 here, but there's not really a need to
	return SoftwareMatcherArgs(get_crc32_for_software_list(data), None, len(data), lambda offset, amount: data[offset:offset+amount])

def get_software_list_entry(game, skip_header=0):
	if game.software_lists:
		software_lists = game.software_lists
	else:
		software_list_names = systems[game.system_name].mame_software_lists
		software_lists = get_software_lists_by_names(software_list_names)

	if game.metadata.media_type == MediaType.OpticalDisc:
		software = None
		if game.rom.extension == 'chd':
			try:
				sha1 = get_sha1_from_chd(game.rom.path)
				args = SoftwareMatcherArgs(None, sha1, None, None)
				software = find_in_software_lists(software_lists, args)
			except UnsupportedCHDError:
				pass
	else:
		if game.subroms:
			#TODO: Get first floppy for now, because right now we don't differentiate with parts or anything; this part of the code sucks
			data = game.subroms[0].read(seek_to=skip_header)
			software = find_in_software_lists(software_lists, matcher_args_for_bytes(data))
		else:
			if skip_header:
				data = game.rom.read(seek_to=skip_header)
				software = find_in_software_lists(software_lists, matcher_args_for_bytes(data))
			else:
				crc32 = format_crc32_for_software_list(game.rom.get_crc32())
				args = SoftwareMatcherArgs(crc32, None, game.rom.get_size(), lambda offset, amount: game.rom.read(seek_to=offset, amount=amount))
				software = find_in_software_lists(software_lists, args)

	if not software and game.system_name in main_config.find_software_by_name:
		software = find_software_by_name(game.software_lists, game.rom.name)

	return software

def format_crc32_for_software_list(crc):
	return '{:08x}'.format(crc)

def get_crc32_for_software_list(data):
	return format_crc32_for_software_list(zlib.crc32(data) & 0xffffffff)

is_release_date_with_thing_at_end = re.compile(r'\d{8}\s\(\w+\)')
def parse_release_date(metadata, release_info):
	if not release_info:
		return

	if is_release_date_with_thing_at_end.match(release_info):
		release_info = release_info[:8]

	if len(release_info) != 8:
		return

	#Some dates contain "x" but like... ehhh, I'll just skip over the unknown parts
	year = release_info[0:4]
	month = release_info[4:6]
	day = release_info[6:8]

	try:
		metadata.year = int(year)
	except ValueError:
		pass
	try:
		metadata.month = calendar.month_name[int(month)]
	except (ValueError, IndexError):
		pass
	try:
		metadata.day = int(day)
	except ValueError:
		pass
