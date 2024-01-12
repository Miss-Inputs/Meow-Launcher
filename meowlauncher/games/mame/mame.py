from meowlauncher.emulator import Emulator
from meowlauncher.games.mame_common.mame_executable import MAMEExecutable


class ConfiguredMAME(Emulator):
	def __init__(self, config):
		self.executable = MAMEExecutable(config.exe_path)
		super().__init__(mame, config)
