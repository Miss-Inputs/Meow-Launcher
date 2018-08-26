import zlib

from metadata import EmulationStatus
from info.system_info import get_mame_software_list_names_by_system_name
from mame_helpers import get_software_lists_by_names, find_in_software_lists, consistentify_manufacturer

#TODO:
#Atari 5200, Colecovision: Try parsing title screen from ROM first
#Intellivison: .int is actually a custom headered file format I think, so that might be tricky to deal with
#Neo Geo CD, CD-i, PC Engine CD, PC-FX: Not sure how well that would work with disc images, since MAME uses <diskarea> and chds there
#Atari 7800: Has header, need to skip it
#NES: Has header, but is stored as split prg/chr inside software lists, need to separate that
#Master System: Hmm, already has a publisher for Game Gear and homebrew... year too
#N64: Not sure if want, this would take 5 hours especially when 7zipped
#Uzebox: .uze files have a header, need to get onto those actually
#ZX Spectrum: All +3 software in MAME is in .ipf format, which seems hardly ever used in all honesty (.z80 files don't have a software list)

def get_software_list_entry(game, skip_header=0):
	software_list_names = get_mame_software_list_names_by_system_name(game.metadata.platform)
	software_lists = get_software_lists_by_names(software_list_names)
	
	crc32 = '{:08x}'.format(zlib.crc32(game.rom.read(seek_to=skip_header)))
	return find_in_software_lists(software_lists, crc=crc32)

def get_part_feature(part, name):
	#TODO: Get sharedfeat from software as well. This isn't used as much though
	for feature in part.findall('feature'):
		if feature.attrib.get('name') == name:
			return feature.attrib.get('value')

	return None

def get_software_info(software, name):
	for info in software.findall('info'):
		if info.attrib.get('name') == name:
			return info.attrib.get('value')

	return None

def add_generic_software_list_info(game, software):
	game.metadata.specific_info['MAME-Software-Name'] = software.attrib.get('name')
	game.metadata.publisher = consistentify_manufacturer(software.findtext('publisher'))
	game.metadata.year = software.findtext('year')
	emulation_status = EmulationStatus.Good
	if 'supported' in software.attrib:
		supported = software.attrib['supported']
		if supported == 'partial':
			emulation_status = EmulationStatus.Imperfect
		elif supported == 'no':
			emulation_status = EmulationStatus.Broken
	game.metadata.specific_info['MAME-Emulation-Status'] = emulation_status
	game.metadata.specific_info['Notes'] = get_software_info(software, 'usage')
	game.metadata.developer = get_software_info(software, 'developer')
	if not game.metadata.developer:
		game.metadata.developer = get_software_info(software, 'author')
