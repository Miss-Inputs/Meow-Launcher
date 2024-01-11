from typing import TYPE_CHECKING

from meowlauncher.configured_emulator import ConfiguredEmulator
from meowlauncher.data.emulators import mame
from meowlauncher.games.mame_common.mame_executable import MAMEExecutable

if TYPE_CHECKING:
	from meowlauncher.config_types import EmulatorConfig


class ConfiguredMAME(ConfiguredEmulator):
	def __init__(self, config: 'EmulatorConfig'):
		self.executable = MAMEExecutable(config.exe_path)
		super().__init__(mame, config)
