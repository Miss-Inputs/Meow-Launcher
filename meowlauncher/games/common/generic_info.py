from collections.abc import Collection
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
	#TODO: Could add "slot" specifically as Mapper?
	#TODO: Is there a better way to handle usage? It would be useful for other specific_behaviours things to use the below stuff but without re-adding usage
	for info_name, info_value in software.infos.items():
		if info_name in {'usage', 'release', 'serial', 'developer', 'alt_title', 'alt_name', 'alt_disk', 'barcode', 'ring_code', 'version', 'video', 'pcb'}:
			#We have already added this
			continue
		metadata.specific_info[info_name.title()] = info_value

def _match_arcade(software_name: str) -> Optional[Machine]:
	try:
		return get_machine(software_name, default_mame_executable)
	except MachineNotFoundException:
		return None

def find_equivalent_arcade_game(game_name: str, game_alt_names: Collection[str], software: 'Software') -> Optional[Machine]:
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

	if machine.family_basename in _not_necessarily_equivalent_arcade_names:
		return None

	if machine.is_pinball:
		#I think not
		return None

	if does_machine_match_name(game_name, machine):
		return machine
	for game_alt_name in game_alt_names:
		if does_machine_match_name(game_alt_name, machine):
			return machine
	return None
