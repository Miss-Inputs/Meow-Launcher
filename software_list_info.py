import zlib
import calendar

from metadata import EmulationStatus
from info.system_info import get_mame_software_list_names_by_system_name
from info.region_info import TVSystem
from mame_helpers import get_software_lists_by_names, consistentify_manufacturer

#TODO: Ideally, every platform wants to be able to get software list info. If available, it will always be preferred over what we can extract from inside the ROMs, as it's more reliable, and avoids the problem of bootlegs/hacks with invalid/missing header data, or publisher/developers that merge and change names and whatnot.
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
#ZX Spectrum: All +3 software in MAME is in .ipf format, which seems hardly ever used in all honesty (.z80 files don't have a software list)

def parse_release_date(game, release_info):
	if not release_info:
		return
	if len(release_info) != 8:
		return

	#TODO: Support dates containing "x", but ehh...
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


class Software():
	def __init__(self, xml, software_list_name=None, software_list_description=None):
		self.xml = xml
		self.has_multiple_parts = len(xml.findall('part')) > 1
		self.software_list_name = software_list_name
		self.software_list_description = software_list_description

	def get_part(self, name=None):
		if name:
			return [part for part in self.xml.findall('part') if part.attrib.get('name') == name][0]
		return self.xml.find('part')

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
		part = self.get_part(part_name)
		for feature in part.findall('feature'):
			if feature.attrib.get('name') == name:
				return feature.attrib.get('value')

		return None

	def has_data_area(self, name, part_name=None):
		part = self.get_part(part_name)
		for data_area in part.findall('dataarea'):
			if data_area.attrib.get('name') == name:
				return True

		return False

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

		if self.software_list_name:
			game.metadata.specific_info['MAME-Software-List-Name'] = self.software_list_name
		if self.software_list_description:
			game.metadata.specific_info['MAME-Software-List-Description'] = self.software_list_description

		publisher = consistentify_manufacturer(self.xml.findtext('publisher'))
		already_has_publisher = game.metadata.publisher and (not game.metadata.publisher.startswith('<unknown'))
		if not (already_has_publisher and (publisher == '<unknown>')):
			game.metadata.publisher = publisher

		compatibility = self.get_shared_feature('compatibility')
		if compatibility == 'PAL':
			game.metadata.tv_type = TVSystem.PAL
		elif compatibility == 'NTSC':
			game.metadata.tv_type = TVSystem.NTSC
		elif compatibility in ('NTSC,PAL', 'PAL,NTSC'):
			game.metadata.tv_type = TVSystem.Agnostic

		game.metadata.year = self.xml.findtext('year')
		parse_release_date(game, self.get_info('release'))

		game.metadata.specific_info['MAME-Emulation-Status'] = self.emulation_status
		game.metadata.specific_info['Notes'] = self.get_info('usage')
		game.metadata.developer = self.get_info('developer')
		if not game.metadata.developer:
			game.metadata.developer = self.get_info('author')
		if not game.metadata.developer:
			game.metadata.developer = self.get_info('programmer')

def _does_rom_match(rom, crc, sha1):
	if sha1:
		if 'sha1' in rom.attrib and rom.attrib['sha1'] == sha1:
			return True
	if crc:
		if 'crc' in rom.attrib and rom.attrib['crc'] == crc:
			return True
	return False

def _does_part_match(part, crc, sha1):
	for data_area in part.findall('dataarea'):
		roms = data_area.findall('rom')
		if not roms:
			#Ignore data areas such as "sram" that don't have any ROMs associated with them.
			#Note that data area's name attribute can be anything like "rom" or "flop" depending on the kind of media, but the element inside will always be called "rom"
			continue
		for rom in roms:
			if _does_rom_match(rom, crc, sha1):
				return True

	return False

def find_in_sofware_list(software_list, crc=None, sha1=None, part_matcher=_does_part_match):
	for software in software_list.findall('software'):
		for part in software.findall('part'):
			#There will be multiple parts sometimes, like if there's multiple floppy disks for one game (will have name = flop1, flop2, etc)
			#diskarea is used instead of dataarea seemingly for CDs or anything else that MAME would use a .chd for in its software list
			if part_matcher(part, crc, sha1):
				return Software(software, software_list.getroot().attrib.get('name'), software_list.getroot().attrib.get('description'))
	return None

def find_in_software_lists(software_lists, crc=None, sha1=None, part_matcher=_does_part_match):
	#TODO: Handle hash collisions. Could happen, even if we're narrowing down to specific software lists
	for software_list in software_lists:
		software = find_in_sofware_list(software_list, crc, sha1, part_matcher)
		if software:
			return software
	return None

def get_software_list_entry(game, skip_header=0):
	if game.software_lists:
		software_lists = game.software_lists
	else:
		software_list_names = get_mame_software_list_names_by_system_name(game.metadata.platform)
		software_lists = get_software_lists_by_names(software_list_names)

	if game.subroms:
		#TODO: Get first floppy for now, because right now we don't differentiate with parts or anything
		data = game.subroms[0].read(seek_to=skip_header)
	else:
		data = game.rom.read(seek_to=skip_header)
	crc32 = '{:08x}'.format(zlib.crc32(data))
	return find_in_software_lists(software_lists, crc=crc32)
