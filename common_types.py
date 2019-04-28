from enum import Enum, auto

class ConfigValueType(Enum):
	Bool = auto()
	FilePath = auto()
	FolderPath = auto()
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

class NotARomException(Exception):
	#File type mismatch, etc
	pass
