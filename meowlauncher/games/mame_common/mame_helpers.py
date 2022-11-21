#Use this file for handy shortcuts with the default MAME config/executable
import functools
from collections.abc import Collection
from pathlib import Path

from .mame_configuration import MAMEConfiguration
from .mame_executable import MAMEExecutable, MAMENotInstalledException

default_mame_executable: MAMEExecutable | None
try:
	default_mame_executable = MAMEExecutable()
except MAMENotInstalledException:
	default_mame_executable = None
default_mame_configuration: MAMEConfiguration | None
try:
	default_mame_configuration = MAMEConfiguration()
except FileNotFoundError:
	default_mame_configuration = None

def have_mame() -> bool:
	return bool(default_mame_executable) and bool(default_mame_configuration)

def verify_software_list(software_list_name: str) -> Collection[str]:
	#TODO: Only used by SoftwareList.available_software - think about where this could be… that is called by mame_software of course, but also emulator_command_line_helpers, hmm
	if not default_mame_executable:
		return set()
	return set(default_mame_executable.verifysoftlist(software_list_name))

@functools.cache
def get_image(config_key: str, machine_or_list_name: str, software_name: str | None=None) -> Path | None:
	if not default_mame_configuration:
		return None
	return default_mame_configuration.get_image(config_key, machine_or_list_name, software_name)

def verify_romset(basename: str) -> bool:
	if not default_mame_executable:
		return False
	return default_mame_executable.verifyroms(basename)
