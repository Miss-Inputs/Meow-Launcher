from enum import Enum, IntEnum, auto

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

class NotLaunchableException(Exception):
	pass

class GameNotSupportedException(NotLaunchableException):
	#Game is not playable for one reason or another, but actually is a game (or other software, for you nitpickers out there)
	pass

class EmulationNotSupportedException(GameNotSupportedException):
	#When a particular emulator does not support this game
	pass

class ExtensionNotSupportedException(EmulationNotSupportedException):
	#Particular emulator does not support this file extension (maybe should be "file type" instead of extension to be more generic)
	pass

class NotActuallyLaunchableGameException(NotLaunchableException):
	#Game is not something that can be launched at all
	pass

class EmulationStatus(IntEnum):
	Good = 2
	Imperfect = 1
	Broken = 0
	Unknown = -1
