import zlib

from metadata import EmulationStatus
from info.system_info import get_mame_software_list_names_by_system_name
from mame_helpers import get_software_lists_by_names, consistentify_manufacturer

#TODO: Ideally, every platform wants to be able to get software list info. If available, it will always be preferred over what we can extract from inside the ROMs, as it's more reliable, and avoids the problem of bootlegs/hacks with invalid/missing header data, or publisher/developers that merge and change names and whatnot.
#We currently do this by putting a block of code inside each platform_metadata helper that does the same thing. I guess I should genericize that one day. Anyway, it's not always possible.

#Because I haven't yet:
#Atari 2600: I guess because Stella's database achieves the same purpose, but yeah, it might be faster actually...

#Has no software list:
#3DS
#DS
#GameCube
#PS2
#PSP
#Wii

#Is optical disc-based, which involves messing around with CHDs (and for that matter, would take a while to calculate the hash):
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

#Roms are big boi and might take a while, especially as they are commonly 7zipped:
#GBA
#N64

#Other difficulties:
#Colecovision: Software list splits 16K roms into multiple halves, making that tricky to deal with. Anyway, can get info unreliably from the title screen info in the ROM
#Intellivison: .int is actually a custom headered file format I think, so that might be tricky to deal with, but I forgot how it works


class Software():
	def __init__(self, xml):
		self.xml = xml
		self.has_multiple_parts = len(xml.findall('part')) > 1

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

		publisher = consistentify_manufacturer(self.xml.findtext('publisher'))
		already_has_publisher = game.metadata.publisher and (not game.metadata.publisher.startswith('<unknown'))
		if not (already_has_publisher and (publisher == '<unknown>')):
			game.metadata.publisher = publisher

		game.metadata.year = self.xml.findtext('year')
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

def find_in_sofware_list(software_list, crc=None, sha1=None):
	for software in software_list.findall('software'):
		for part in software.findall('part'):
			#There will be multiple parts sometimes, like if there's multiple floppy disks for one game (will have name = flop1, flop2, etc)
			#diskarea is used instead of dataarea seemingly for CDs or anything else that MAME would use a .chd for in its software list
			if _does_part_match(part, crc, sha1):
				return Software(software)	
	return None

def find_in_software_lists(software_lists, crc=None, sha1=None):
	#TODO: Handle hash collisions. Could happen, even if we're narrowing down to specific software lists
	for software_list in software_lists:
		software = find_in_sofware_list(software_list, crc, sha1)
		if software:
			return software
	return None

def get_software_list_entry(game, skip_header=0):
	if game.software_lists:
		software_lists = game.software_lists
	else:
		software_list_names = get_mame_software_list_names_by_system_name(game.metadata.platform)
		software_lists = get_software_lists_by_names(software_list_names)
	
	crc32 = '{:08x}'.format(zlib.crc32(game.rom.read(seek_to=skip_header)))
	return find_in_software_lists(software_lists, crc=crc32)
