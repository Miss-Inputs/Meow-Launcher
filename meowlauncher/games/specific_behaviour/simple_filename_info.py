"""Where we just want to detect stuff from filename tags, nothing fancy"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Sequence

	from meowlauncher.info import GameInfo


def _atari_st_machine_from_tags(tags: 'Sequence[str]') -> str | None:
	if '(Mega ST)' in tags:
		return 'Mega ST'
	if '(Mega-STE)' in tags:
		return 'Mega STe'
	if '(ST)' in tags:
		return 'ST'
	if '(STe)' in tags:
		return 'STe'
	if '(STE-Falcon)' in tags:
		return 'Falcon'  # TODO: This might be meant to be read as "STE/Falcon"
	if '(TT)' in tags:
		return 'TT'

	# Not all are in the TOSEC naming standard, but might appear in a filename for lack of a better place to have that info
	if '(Falcon)' in tags:
		return 'Falcon'
	if '(Falcon030)' in tags:
		return 'Falcon030'
	return None


def add_atari_st_info(tags: 'Sequence[str]', metadata: 'GameInfo') -> None:
	"""Sets intended machine (ST, STe, Falcon, etc) according to filename"""
	machine = _atari_st_machine_from_tags(tags)
	if machine:
		metadata.specific_info['Machine'] = machine
