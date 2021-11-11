from enum import Enum, IntEnum, auto

class ConfigValueType(Enum):
	Bool = auto()
	FilePath = auto()
	FolderPath = auto()
	Integer = auto()
	String = auto()
	StringList = auto()
	FilePathList = auto()
	FolderPathList = auto()

class MediaType(Enum):
	Cartridge = auto()
	Digital = auto()
	Executable = auto()
	Floppy = auto()
	HardDisk = auto()
	OpticalDisc = auto()
	Tape = auto()
	Snapshot = auto()
	Barcode = auto()
	Standalone = auto()

class SaveType(Enum):
	Nothing = auto()
	Cart = auto()
	Floppy = auto()
	MemoryCard = auto()
	Internal = auto()
	Cloud = auto()
	Unknown = auto()

class EmulationNotSupportedException(Exception):
	pass

class ExtensionNotSupportedException(EmulationNotSupportedException):
	pass

class NotARomException(Exception):
	#File type mismatch, etc
	pass

class EmulationStatus(IntEnum):
	Good = 2
	Imperfect = 1
	Broken = 0
	Unknown = -1

class EmulatorStatus(Enum):
	#I have not actually thought of concrete definitions for what these mean
	Good = 6
	Imperfect = 5
	ExperimentalButSeemsOkay = 4
	Experimental = 3
	Janky = 2 #Weird to set up or launch normally
	Borked = 1

class EmulatorPlatform():
	Native = auto()
	Windows = auto()
	DotNet = auto()
