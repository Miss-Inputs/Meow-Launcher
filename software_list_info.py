import zlib
import calendar
import xml.etree.ElementTree as ElementTree
import os

from metadata import EmulationStatus
from info.system_info import systems
from info.region_info import TVSystem
from mame_helpers import consistentify_manufacturer, get_mame_config

#Ideally, every platform wants to be able to get software list info. If available, it will always be preferred over what we can extract from inside the ROMs, as it's more reliable, and avoids the problem of bootlegs/hacks with invalid/missing header data, or publisher/developers that merge and change names and whatnot.
#We currently do this by putting a block of code inside each platform_metadata helper that does the same thing. I guess I should genericize that one day. Anyway, it's not always possible.

#Has no software list:
#3DS
#DS
#GameCube
#PS2
#PSP
#Wii

#Is optical disc-based, which involves messing around with CHDs (and for that matter, would take a while to calculate the hash); I'm not sure how it would work exactly because it seems the sha1 of the whole CHD file (as listed in chdman, which is different from if you tried to checksum the file yourself) has to match the <diskarea> rom instead of the data hash which is also in the CHD header:
#Amiga CD32
#CD-i
#Dreamcast
#Mega CD
#Neo Geo CD
#PC Engine CD
#PC-FX
#PS1
#Saturn

#Has a software list, but not for the formats we use:
#VZ-200: .vz doesn't have a software list

def parse_size_attribute(attrib):
	if not attrib:
		return None
	return int(attrib, 16 if attrib.startswith('0x') else 10)

class DataAreaROM():
	def __init__(self, xml, data_area):
		self.xml = xml
		self.data_area = data_area

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

class SoftwarePart():
	def __init__(self, xml, software):
		self.xml = xml
		self.software = software
		self.data_areas = {}

		for data_area_xml in self.xml.findall('dataarea'):
			data_area = DataArea(data_area_xml, self)
			self.data_areas[data_area.name] = data_area

	@property
	def name(self):
		return self.xml.attrib.get('name')

	def get_feature(self, name):
		for feature in self.xml.findall('feature'):
			if feature.attrib.get('name') == name:
				return feature.attrib.get('value')

		return None

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
		elif supported == 'no':
			return EmulationStatus.Broken

		#Supported = "yes"
		return EmulationStatus.Good

	def add_generic_info(self, game):
		game.metadata.specific_info['MAME-Software-Name'] = self.xml.attrib.get('name')
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

def _does_rom_match(rom, crc32, sha1):
	if sha1:
		if rom.sha1 == sha1:
			return True
	if crc32:
		if rom.crc32 == crc32:
			return True
	return False

def _does_split_rom_match(part, data, _):
	rom_data_area = None
	for data_area in part.data_areas.values():
		if data_area.name == 'rom':
			rom_data_area = data_area
			break
	if not rom_data_area:
		return False

	if rom_data_area.size != len(data):
		return False

	for rom_segment in rom_data_area.roms:
		if not rom_segment.name and not rom_segment.crc32:
			continue

		offset = rom_segment.offset
		size = rom_segment.size

		try:
			chunk = data[offset:offset+size]
		except IndexError:
			return False
		chunk_crc32 = '{:08x}'.format(zlib.crc32(chunk))
		if rom_segment.crc32 != chunk_crc32:
			return False

	return True

def _does_part_match(part, crc, sha1):
	for data_area in part.data_areas.values():
		roms = data_area.roms
		if not roms:
			#Ignore data areas such as "sram" that don't have any ROMs associated with them.
			#Note that data area's name attribute can be anything like "rom" or "flop" depending on the kind of media, but the element inside will always be called "rom"
			continue
		for rom in roms:
			if _does_rom_match(rom, crc, sha1):
				return True

	return False

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

	def find_software(self, part_matcher=_does_part_match, part_matcher_args=None):
		if part_matcher_args is None:
			part_matcher_args = ()

		for software_xml in self.xml.findall('software'):
			software = Software(software_xml, self)
			for part in software.parts.values():
				#There will be multiple parts sometimes, like if there's multiple floppy disks for one game (will have name = flop1, flop2, etc)
				#diskarea is used instead of dataarea seemingly for CDs or anything else that MAME would use a .chd for in its software list
				if part_matcher(part, *part_matcher_args):
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

def find_in_software_lists(software_lists, crc=None, sha1=None, part_matcher=_does_part_match):
	#TODO: Handle hash collisions. Could happen, even if we're narrowing down to specific software lists
	for software_list in software_lists:
		software = software_list.find_software(part_matcher, (crc, sha1))
		if software:
			return software
	return None

def get_software_list_entry(game, skip_header=0):
	if game.software_lists:
		software_lists = game.software_lists
	else:
		software_list_names = systems[game.metadata.platform].mame_software_lists
		software_lists = get_software_lists_by_names(software_list_names)

	if game.subroms:
		#TODO: Get first floppy for now, because right now we don't differentiate with parts or anything
		data = game.subroms[0].read(seek_to=skip_header)
	else:
		data = game.rom.read(seek_to=skip_header)
	crc32 = get_crc32_for_software_list(data)
	software = find_in_software_lists(software_lists, crc=crc32)
	if not software:
		software = find_in_software_lists(software_lists, crc=data, part_matcher=_does_split_rom_match)
	return software

def get_crc32_for_software_list(data):
	return '{:08x}'.format(zlib.crc32(data))

def parse_release_date(game, release_info):
	if not release_info:
		return
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
