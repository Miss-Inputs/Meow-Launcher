from meowlauncher.common_types import ConfigValueType

class EmulatorConfig():
	def __init__(self, name: str):
		self.name = name
		self.exe_path = None
		self.options: dict[str, EmulatorConfigValue] = {}

class EmulatorConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	def __init__(self, value_type: ConfigValueType, default_value, description: str):
		self.type = value_type
		self.default_value = default_value
		self.description = description
