from typing import Any, Optional

from meowlauncher.common_types import ConfigValueType

class RunnerConfig():
	def __init__(self, name: str):
		self.name = name
		self.exe_path: Optional[str] = None
		self.options: dict[str, EmulatorConfigValue] = {}

#Hmm pointless class so far… what am I doing
class EmulatorConfig(RunnerConfig):
	pass
	
class EmulatorConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	def __init__(self, value_type: ConfigValueType, default_value: Any, description: str):
		self.type = value_type
		self.default_value = default_value
		self.description = description
