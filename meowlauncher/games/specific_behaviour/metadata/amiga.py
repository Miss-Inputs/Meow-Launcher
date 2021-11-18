from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

def add_amiga_metadata_from_software_list(software: 'Software', metadata: 'Metadata'):
	chipset = None
	if software:
		software.add_standard_metadata(metadata)
		chipset = 'OCS'
		usage = software.get_info('usage')
		if usage in {'Requires ECS', 'Requires ECS, includes Amiga Text'}:
			chipset = 'ECS'
		elif usage == 'Requires AGA':
			chipset = 'AGA'
		else:
			#The remainder is something like "Requires <some other software> to work", because it's a level editor or save editor or something like that
			metadata.add_notes(usage)

		#info name="additional":
		#Features Kid Gloves demo
		#Features StarRay demo
		#Features XR35 and KGP demos
		#Mastered with virus
		#info name="alt_disk": Names of some disks?
		#info name="magazine": What magazine it came from?
	metadata.specific_info['Chipset'] = chipset

def add_info_from_filename_tags(tags: Iterable[str], metadata: 'Metadata'):
	for tag in tags:
		if tag == '[HD]':
			metadata.specific_info['Requires Hard Disk?'] = True
			continue
		if tag == '[WB]':
			metadata.specific_info['Requires Workbench?'] = True
			continue
		
		models = {'A1000', 'A1200', 'A4000', 'A2000', 'A3000', 'A3000UX', 'A2024', 'A2500', 'A4000T', 'A500', 'A500+', 'A570', 'A600', 'A600HD'}
		for model in models:
			if tag == ('(%s)' % model):
				metadata.specific_info['Machine'] = model

		#This should set machine to an array or something-separated list, tbh
		if tag == '(A1200-A4000)':
			metadata.specific_info['Machine'] = 'A4000'
		elif tag == '(A2000-A3000)':
			metadata.specific_info['Machine'] = 'A3000'
		elif tag == '(A2500-A3000UX)':
			metadata.specific_info['Machine'] = 'A3000UX'
		elif tag == '(A500-A1000-A2000)':
			metadata.specific_info['Machine'] = 'A2000'
		elif tag == '(A500-A1000-A2000-CDTV)':
			metadata.specific_info['Machine'] = 'A2000'
		elif tag == '(A500-A1200)':
			metadata.specific_info['Machine'] = 'A1200'
		elif tag == '(A500-A2000)':
			metadata.specific_info['Machine'] = 'A2000'
		elif tag == '(A500-A600-A2000)':
			metadata.specific_info['Machine'] = 'A2000'
		elif tag == '(A500-A1200-A2000-A4000)':
			metadata.specific_info['Machine'] = 'A4000'
			
	if 'Chipset' not in metadata.specific_info:
		chipset = None
		for tag in tags:
			if tag in {'(AGA)', '(OCS-AGA)', '(ECS-AGA)', '(AGA-CD32)'}:
				chipset = 'AGA'
				break
			if tag in {'(ECS)', '(ECS-OCS)'}:
				chipset = 'ECS'
				break
			if tag == '(OCS)':
				chipset = 'OCS'
				break
		if chipset:
			metadata.specific_info['Chipset'] = chipset

def add_amiga_metadata(game: 'ROMGame'):
	software = game.get_software_list_entry()
	if software:
		add_amiga_metadata_from_software_list(software, game.metadata)
		
	add_info_from_filename_tags(game.filename_tags, game.metadata)
	