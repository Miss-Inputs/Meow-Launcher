from typing import TYPE_CHECKING, Optional

from meowlauncher.games.mame_common.machine import (Machine,
                                                    does_machine_match_name,
                                                    get_machine)
from meowlauncher.games.mame_common.mame_executable import \
    MachineNotFoundException
from meowlauncher.games.mame_common.mame_helpers import default_mame_executable
from meowlauncher.util.region_info import TVSystem
from meowlauncher.util.utils import load_list

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata
	
_not_necessarily_equivalent_arcade_names = load_list(None, 'not_necessarily_equivalent_arcade_names')

def add_generic_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	metadata.add_notes(software.get_info('usage'))
	if 'pcb' in software.infos:
		metadata.specific_info['PCB'] = software.get_info('pcb')
	metadata.specific_info['Requirement'] = software.get_shared_feature('requirement')
	try:
		metadata.specific_info['TV Type'] = TVSystem(software.get_info('video'))
	except ValueError:
		pass
	for info_name, info_value in software.infos.items():
		if info_name in {'usage', 'release', 'serial', 'developer', 'alt_title', 'alt_name', 'alt_disk', 'barcode', 'ring_code', 'version', 'video', 'pcb'}:
			#We have already added this
			continue
		metadata.specific_info[info_name.replace('_', '-').replace(' ', '-').title()] = info_value

def _match_arcade(software_name: str) -> Optional[Machine]:
	try:
		return get_machine(software_name, default_mame_executable)
	except MachineNotFoundException:
		return None

def find_equivalent_arcade_game(game: 'ROMGame', software: 'Software') -> Optional[Machine]:
	#Just to be really strict: We will only get it if the software name matches
	if not default_mame_executable:
		return None
	if software.name in _not_necessarily_equivalent_arcade_names or software.parent_name in _not_necessarily_equivalent_arcade_names:
		return None

	machine = _match_arcade(software.name)
	if not machine and software.parent_name:
		machine = _match_arcade(software.parent_name)
	if not machine:
		return None

	if machine.family in _not_necessarily_equivalent_arcade_names:
		return None

	# catlist = machine.catlist
	# if catlist and not catlist.is_arcade:
	# 	#I think not, only video games can be video games
	# 	#That comment made sense but y'know what I mean right
	# 	#Do we really need to exclude mechanical/slot machines? This function used to, I dunno
	# 	return None
	#if '(bootleg of' in machine.name or '(bootleg?)' in machine.name:
	#	#This doesn't count
	#	#Why doesn't it?
	#	return None

	if does_machine_match_name(game.name, machine):
		return machine
	for game_name in game.metadata.names.values():
		if does_machine_match_name(game_name, machine):
			return machine
	return None
