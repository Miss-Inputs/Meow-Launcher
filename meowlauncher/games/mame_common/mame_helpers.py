"""#Use this file for handy shortcuts with the default MAME config/executable
But also don't because relying on default_mame_executable is a bit ehh"""
import functools
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


@functools.cache
def get_image(
	config_key: str, machine_or_list_name: str, software_name: str | None = None
) -> Path | None:
	if not default_mame_configuration:
		return None
	return default_mame_configuration.get_image(config_key, machine_or_list_name, software_name)
