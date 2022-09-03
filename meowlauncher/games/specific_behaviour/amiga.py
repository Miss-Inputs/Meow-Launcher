from collections.abc import Collection
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

def add_amiga_metadata_from_software_list(software: 'Software', metadata: 'Metadata') -> None:
	software.add_standard_metadata(metadata)
	chipset = None

	if software.software_list_name == 'amigaaga_flop':
		chipset = 'AGA'
	elif software.software_list_name == 'amigaecs_flop':
		chipset = 'ECS'
	elif software.software_list_name == 'amigaocs_flop':
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
	if chipset:
		metadata.specific_info['Chipset'] = chipset

def _machine_from_tag(tag: str) -> Optional[str | Collection[str]]:
	#As listed in TOSEC naming convention
	tag = tag[1:-1]

	models = {'A1000', 'A1200', 'A4000', 'A2000', 'A3000', 'A3000UX', 'A2024', 'A2500', 'A4000T', 'A500', 'A500+', 'A570', 'A600', 'A600HD', 'CD32'}
	if tag in models:
		return tag
	
	split_models = {'A1200-A4000', 'A2000-A3000', 'A2500-A3000UX', 'A500-A1000-A2000', 'A500-A1000-A2000-CDTV', 'A500-A1200', 'A500-A2000', 'A500-A600-A2000', 'A500-A1200-A2000-A4000'}
	if tag in split_models:
		return tag.split('-')
	return None

def _chipset_from_tag(tag: str) -> Optional[str | Collection[str]]:
	if tag == 'AGA':
		return 'AGA'
	if tag == '(OCS-AGA)':
		return ('OCS', 'AGA') #hmm, does this imply it's just not compatible with ECS?
	if tag == '(ECS-AGA)':
		return ('ECS', 'AGA')
	if tag == '(AGA-CD32)':
		#Hmm… CD32 is really more what I'd put under "machine" rather than "chipset", I guess…
		#This probably won't matter too much though, when do you even see this combination?
		return ('AGA', 'CD32')
	if tag == '(ECS)':
		return 'ECS'
	if tag == '(ECS-OCS)':
		return ('ECS', 'OCS')
	if tag == '(OCS)':
		return 'OCS'
	return None

def add_info_from_filename_tags(tags: Collection[str], metadata: 'Metadata') -> None:
	for tag in tags:
		if tag == '[HD]':
			metadata.specific_info['Requires Hard Disk?'] = True
			continue
		if tag == '[WB]':
			metadata.specific_info['Requires Workbench?'] = True
			continue
		if tag == '[AMOS]':
			metadata.specific_info['Uses AMOS?'] = True
			continue
		if tag == '[KS 1.2]':
			metadata.specific_info['Kickstart Version'] = 'v1.2'
			continue
		if tag == '(68060)':
			#Not in TOSEC, but probably good to use something to indicate it requires funny CPUs
			metadata.specific_info['Minimum CPU'] = '68080'
			continue
		if tag == '(SEUCK)':
			metadata.specific_info['Engine'] = 'Shoot-\'Em-Up Construction Kit'
			continue
		if tag == '(3DCK)':
			metadata.specific_info['Engine'] = '3D Construction Kit'
			continue
		
		if 'Machine' not in metadata.specific_info:
			machine = _machine_from_tag(tag)
			if machine:
				metadata.specific_info['Machine'] = machine
			
		if 'Chipset' not in metadata.specific_info:
			chipset = _chipset_from_tag(tag)
			if chipset:
				metadata.specific_info['Chipset'] = chipset
		

def add_amiga_custom_info(game: 'ROMGame') -> None:
	software = game.get_software_list_entry()
	if software:
		add_amiga_metadata_from_software_list(software, game.metadata)
		
	add_info_from_filename_tags(game.filename_tags, game.metadata)
	