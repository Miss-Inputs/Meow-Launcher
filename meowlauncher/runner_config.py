from typing import Any

from meowlauncher.common_types import ConfigValueType

class RunnerConfig():
	def __init__(self, exe_path: str=None, options=dict[str, 'RunnerConfigValue']):
		self.exe_path = exe_path
		self.options = options

#Hmm pointless class so far… what am I doing
class EmulatorConfig(RunnerConfig):
	pass
	
class RunnerConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	def __init__(self, value_type: ConfigValueType, default_value: Any, description: str):
		self.type = value_type
		self.default_value = default_value
		self.description = description
