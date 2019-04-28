import zlib
import calendar
import xml.etree.ElementTree as ElementTree
import os
import re

from metadata import EmulationStatus
from info.system_info import systems
from info.region_info import TVSystem
from mame_helpers import consistentify_manufacturer, get_mame_config
from common_types import MediaType
import io_utils

#Ideally, every platform wants to be able to get software list info. If available, it will always be preferred over what we can extract from inside the ROMs, as it's more reliable, and avoids the problem of bootlegs/hacks with invalid/missing header data, or publisher/developers that merge and change names and whatnot.
#We currently do this by putting a block of code inside each platform_metadata helper that does the same thing. I guess I should genericize that one day. Anyway, it's not always possible.

#Has no software list:
#3DS
#DS
#GameCube
#PS2
#PSP
#Wii

def parse_size_attribute(attrib):
	if not attrib:
		return None
	return int(attrib, 16 if attrib.startswith('0x') else 10)

class DataAreaROM():
	def __init__(self, xml, data_area):
		self.xml = xml
		self.data_area = data_area
	#Other properties as defined in DTD: length (what's the difference with size?), status (baddump/nodump/good), loadflag (probably not needed for our purposes)

	@property
	def name(self):
		return self.xml.attrib.get('name')

	@property
	def size(self):
		return parse_size_attribute(self.xml.attrib.get('size'))

	@property
	def crc32(self):
		return self.xml.attrib.get('crc')
	
	@property
	def sha1(self):
		return self.xml.attrib.get('sha1')

	@property
	def offset(self):
		return parse_size_attribute(self.xml.attrib.get('offset'))

	def matches(self, crc32, sha1):
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
		return parse_size_attribute(self.xml.attrib.get('size'))

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
					return False

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
	
	#There is also status (baddump/nodump/good)

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

class Software():
	def __init__(self, xml, software_list):
		self.xml = xml
		self.software_list = software_list

		self.parts = {}
		for part_xml in self.xml.findall('part'):
			part = SoftwarePart(part_xml, self)
			self.parts[part.name] = part

	@property
	def name(self):
		return self.xml.attrib.get('name')

	@property
	def software_list_name(self):
		return self.software_list.name

	@property
	def has_multiple_parts(self):
		return len(self.parts) > 1

	def get_part(self, name=None):
		if name:
			return self.parts[name]
		return SoftwarePart(self.xml.find('part'), self)

	def get_info(self, name):
		for info in self.xml.findall('info'):
			if info.attrib.get('name') == name:
				return info.attrib.get('value')

		return None

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

	def add_generic_info(self, game):
		game.metadata.specific_info['MAME-Software-Name'] = self.name
		game.metadata.specific_info['MAME-Software-Full-Name'] = self.xml.findtext('description')

		cloneof = self.xml.attrib.get('cloneof')
		if cloneof:
			game.metadata.specific_info['MAME-Software-Parent'] = cloneof

		game.metadata.specific_info['MAME-Software-List-Name'] = self.software_list.name
		game.metadata.specific_info['MAME-Software-List-Description'] = self.software_list.description

		serial = self.get_info('serial')
		if serial:
			game.metadata.product_code = serial

		compatibility = self.get_shared_feature('compatibility')
		if compatibility == 'PAL':
			game.metadata.tv_type = TVSystem.PAL
		elif compatibility == 'NTSC':
			game.metadata.tv_type = TVSystem.NTSC
		elif compatibility in ('NTSC,PAL', 'PAL,NTSC'):
			game.metadata.tv_type = TVSystem.Agnostic

		year = self.xml.findtext('year')
		if game.metadata.year:
			already_has_valid_year = '?' not in game.metadata.year if isinstance(game.metadata.year, str) else True
		else:
			already_has_valid_year = False
		if not ('?' in year and already_has_valid_year):
			game.metadata.year = year
		parse_release_date(game, self.get_info('release'))

		game.metadata.specific_info['MAME-Emulation-Status'] = self.emulation_status
		developer = consistentify_manufacturer(self.get_info('developer'))
		if not developer:
			developer = consistentify_manufacturer(self.get_info('author'))
		if not developer:
			developer = consistentify_manufacturer(self.get_info('programmer'))
		if developer:
			game.metadata.developer = developer

		publisher = consistentify_manufacturer(self.xml.findtext('publisher'))
		already_has_publisher = game.metadata.publisher and (not game.metadata.publisher.startswith('<unknown'))
		if publisher in ('<doujin>', '<homebrew>', '<unlicensed>') and developer:
			game.metadata.publisher = developer
		elif not (already_has_publisher and (publisher == '<unknown>')):
			game.metadata.publisher = publisher

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
		mame_config = get_mame_config()
		for hash_path in mame_config.settings['hashpath']:
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
		software_list_names = systems[game.metadata.platform].mame_software_lists
		software_lists = get_software_lists_by_names(software_list_names)

	if game.metadata.media_type == MediaType.OpticalDisc:
		if game.rom.extension == 'chd':
			try:
				sha1 = get_sha1_from_chd(game.rom.path)
				args = SoftwareMatcherArgs(None, sha1, None, None)
				return find_in_software_lists(software_lists, args)
			except UnsupportedCHDError:
				pass
		return None

	if game.subroms:
		#TODO: Get first floppy for now, because right now we don't differentiate with parts or anything; this part of the code sucks
		#TODO: Subroms for chds, just to make my head explode more
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
	return software

def format_crc32_for_software_list(crc):
	return '{:08x}'.format(crc)

def get_crc32_for_software_list(data):
	return format_crc32_for_software_list(zlib.crc32(data) & 0xffffffff)

is_release_date_with_thing_at_end = re.compile(r'\d{8}\s\(\w+\)')
def parse_release_date(game, release_info):
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
		game.metadata.year = int(year)
	except ValueError:
		pass
	try:
		game.metadata.month = calendar.month_name[int(month)]
	except (ValueError, IndexError):
		pass
	try:
		game.metadata.day = int(day)
	except ValueError:
		pass
