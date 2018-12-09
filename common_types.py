from enum import Enum, auto

class ConfigValueType(Enum):
	Bool = auto()
	Path = auto()
	String = auto()
	StringList = auto()
	PathList = auto()
