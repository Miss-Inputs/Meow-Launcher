from meowlauncher.common_types import ConfigValueType, TypeOfConfigValue

class RunnerConfig():
	def __init__(self, exe_path: str, options: dict[str, TypeOfConfigValue]=None):
		self.exe_path = exe_path
		self.options = options if options else {}

#Hmm pointless class so far… what am I doing
class EmulatorConfig(RunnerConfig):
	pass
	
class RunnerConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	def __init__(self, value_type: ConfigValueType, default_value: TypeOfConfigValue, description: str):
		self.type = value_type
		self.default_value = default_value
		self.description = description
