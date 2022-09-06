from collections.abc import Collection, Sequence
from functools import lru_cache
from typing import TYPE_CHECKING, Optional

from meowlauncher.games.mame_common.machine import (Machine,
                                                    does_machine_match_name,
                                                    get_machine)
from meowlauncher.games.mame_common.mame_executable import \
    MachineNotFoundException
from meowlauncher.games.mame_common.mame_helpers import default_mame_executable
from meowlauncher.util.detect_things_from_filename import (
    get_date_from_filename_tags, get_languages_from_filename_tags,
    get_license_from_filename_tags, get_regions_from_filename_tags,
    get_revision_from_filename_tags, get_version_from_filename_tags)
from meowlauncher.util.region_info import TVSystem
from meowlauncher.util.utils import load_list

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.metadata import Metadata
	
_not_necessarily_equivalent_arcade_names = load_list(None, 'not_necessarily_equivalent_arcade_names')

def add_generic_software_info(software: 'Software', metadata: 'Metadata') -> None:
	software.add_standard_metadata(metadata)
	metadata.add_notes(software.get_info('usage'))
	metadata.add_notes(software.get_info('comment'))
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
		if info_name in {'usage', 'comment', 'release', 'serial', 'developer', 'alt_title', 'alt_name', 'alt_disk', 'barcode', 'ring_code', 'version', 'video', 'pcb'}:
			#We have already added this
			continue
		metadata.specific_info[info_name.title()] = info_value

@lru_cache(maxsize=5) #We don't want to hold onto Machine objects forever, the maxsize is how many times we expect software with the same basename to be called in a row, which is only a handful at most (I guess it would happen if you have a bunch of games in the same directory with the same software parent?)
def _match_arcade(software_name: str) -> Optional[Machine]:
	assert default_mame_executable, 'We are only calling this from a method that already checked…'
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

def add_dump_status_info_from_tags(tags: Sequence[str], metadata: 'Metadata') -> None:
	#"As noted at the start of Single Image Sets chapter, the order of those flags is important and
	#should be kept correct. The order should always be:
	#[cr][f][h][m][p][t][tr][o][u][v][b][a][!]"
	#In case that matters to anyone, but it doesn't
	for tag in tags:
		if tag.startswith('[cr '):
			metadata.specific_info['Cracked By'] = tag.removeprefix('[cr ')[:-1]
			metadata.specific_info.setdefault('Bad Dump', set()).add('Cracked')
		if tag == '[cr' and (tag[2] == ']' or tag[2].isdigit()):
			metadata.specific_info.setdefault('Bad Dump', set()).add('Cracked')
		if tag.startswith('[b '):
			metadata.specific_info.setdefault('Bad Dump', set()).add(tag.removeprefix('[b ')[:-1])
		elif tag.startswith('[b') and (tag[2] == ']' or tag[2].isdigit()):
			metadata.specific_info.setdefault('Bad Dump', set()).add('Bad Dump')
		if tag.startswith('[f '):
			#Well, this is a problem - you cannot parse any difference between what the fix is, and who the fix is by
			fix_description = tag.removeprefix('[f ')[:-1]
			#Let's do some silly assumptions that anything lowercase is a fix and anything Title Case is the name of the person/group
			if fix_description.istitle():
				metadata.specific_info['Fixed By'] = fix_description
			else:
				metadata.specific_info['Fix'] = fix_description
		elif tag.startswith('[f') and (tag[2] == ']' or tag[2].isdigit()):
			#Actually, we won't consider this to be a "bad dump"
			metadata.specific_info['Fix'] = True
		#if tag.startswith('[f'):
		#	metadata.specific_info.setdefault('Bad Dump', set()).add('Fixed')
		if tag.startswith('[h '):
			#Same shenanigans here…
			hack_description = tag.removeprefix('[h ')[:-1]
			if hack_description.istitle():
				metadata.specific_info['Hacked By'] = hack_description
			else:
				metadata.specific_info['Hack'] = hack_description
			metadata.specific_info.setdefault('Bad Dump', set()).add('Hacked')
		if tag.startswith('[h') and (tag[2] == ']' or tag[2].isdigit()):
			metadata.specific_info.setdefault('Bad Dump', set()).add('Hacked')
		if tag.startswith('[m '):
			#TOSEC says this is called "modified", but then it means some disk image that is unclean (contains a save file etc), which others would call a bad dump
			metadata.specific_info.setdefault('Bad Dump', set()).add(tag.removeprefix('[m ')[:-1])
		elif tag.startswith('[m') and (tag[2] == ']' or tag[2].isdigit()):
			metadata.specific_info.setdefault('Bad Dump', set()).add('Unclean')
		if tag.startswith('[t '):
			trainer_description = tag.removeprefix('[t ')[:-1]
			if trainer_description.startswith('+'):
				if ' ' in trainer_description:
					number_of_trainers, trained_by = trainer_description.split(' ', 1)
					metadata.specific_info.setdefault('Bad Dump', set()).add(f'{number_of_trainers} Trainers')
					metadata.specific_info['Trained By'] = trained_by
				else:
					metadata.specific_info.setdefault('Bad Dump', set()).add(f'{trainer_description} Trainers')
			else:
				metadata.specific_info['Trained By'] = trainer_description
				metadata.specific_info.setdefault('Bad Dump', set()).add('Trainer')
		elif tag.startswith('[t') and (tag[2] == ']' or tag[2].isdigit()):
			metadata.specific_info.setdefault('Bad Dump', set()).add('Trainer')
		if tag.startswith('[o') and (tag[2] == ']' or tag[2].isdigit()):
			metadata.specific_info.setdefault('Bad Dump', set()).add('Overdump')
		if tag.startswith('[u') and (tag[2] == ']' or tag[2].isdigit()):
			metadata.specific_info.setdefault('Bad Dump', set()).add('Underdump')
		if tag.startswith('[v '):
			metadata.specific_info['Virus'] = tag.removeprefix('[v ')[:-1]
			metadata.specific_info.setdefault('Bad Dump', set()).add('Virus')
		if tag.startswith('[v') and (tag[2] == ']' or tag[2].isdigit()):
			metadata.specific_info.setdefault('Bad Dump', set()).add('Virus')
		
		#TODO: Find something to do with [p], [p (group/person], (Pirate), (Unl)
		#(Aftermarket)
		#(Demo) (Beta) (Proto) etc etc
		#(Alt) [a] etc etc

def add_generic_info_from_filename_tags(tags: Sequence[str], metadata: 'Metadata') -> None:
	filename_date = get_date_from_filename_tags(tags)
	if filename_date:
		if filename_date.is_better_than(metadata.release_date):
			metadata.release_date = filename_date
	
	if 'Revision' not in metadata.specific_info:
		metadata.specific_info['Revision'] = get_revision_from_filename_tags(tags)

	if 'Version' not in metadata.specific_info:
		metadata.specific_info['Version'] = get_version_from_filename_tags(tags)

	if not metadata.regions:
		regions = get_regions_from_filename_tags(tags)
		if regions:
			metadata.regions = regions

	if not metadata.languages:
		languages = get_languages_from_filename_tags(tags)
		if languages:
			metadata.languages = languages

	if 'License' not in metadata.specific_info:
		metadata.specific_info['License'] = get_license_from_filename_tags(tags)

	add_dump_status_info_from_tags(tags, metadata)

	for tag in tags:
		if tag.startswith('[aka '):
			metadata.add_alternate_name(tag.removeprefix('[aka ')[:-1])
		if tag.lower().startswith('[req '):
			requirement = tag[len('[req '):-1]
			existing_requirement = metadata.specific_info.get('Requirement')
			if existing_requirement:
				if requirement not in existing_requirement:
					metadata.specific_info['Requirement'] = f'{existing_requirement}, {requirement}'
			else:
				metadata.specific_info['Requirement'] = requirement
