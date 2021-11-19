#Use this file for handy shortcuts with the default MAME config/executable
import functools
from collections.abc import Collection
from pathlib import Path
from typing import Optional

from .mame_configuration import MAMEConfiguration
from .mame_executable import MAMEExecutable, MAMENotInstalledException


class DefaultMameExecutable():
	__instance = None
	__missing = False

	@staticmethod
	def getDefaultMameExecutable():
		if DefaultMameExecutable.__instance is None and not DefaultMameExecutable.__missing:
			try:
				DefaultMameExecutable.__instance = MAMEExecutable()
			except MAMENotInstalledException:
				DefaultMameExecutable.__missing = True
				return None
		return DefaultMameExecutable.__instance

class DefaultMameConfiguration():
	__instance = None
	__missing = False

	@staticmethod
	def getDefaultMameConfiguration():
		if DefaultMameConfiguration.__instance is None and not DefaultMameConfiguration.__missing:
			try:
				DefaultMameConfiguration.__instance = MAMEConfiguration()
			except FileNotFoundError:
				DefaultMameConfiguration.__missing = True
				return None
		return DefaultMameConfiguration.__instance	

default_mame_executable = DefaultMameExecutable.getDefaultMameExecutable()
default_mame_configuration = DefaultMameConfiguration.getDefaultMameConfiguration()

def have_mame() -> bool:
	return bool(default_mame_executable) and bool(default_mame_configuration)

def verify_software_list(software_list_name: str) -> Collection[str]:
	#TODO: Only used by SoftwareList.get_available_software - think about where this could be… that is called by mame_software of course, but also emulator_command_line_helpers, hmm
	return set(default_mame_executable.verifysoftlist(software_list_name))

@functools.cache
def get_image(config_key: str, machine_or_list_name: str, software_name: Optional[str]=None) -> Optional[Path]:
	return default_mame_configuration.get_image(config_key, machine_or_list_name, software_name)

def verify_romset(basename: str) -> bool:
	return default_mame_executable.verifyroms(basename)
