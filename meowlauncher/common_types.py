from enum import Enum, IntEnum, auto

from meowlauncher.util.utils import format_byte_size


class ByteAmount(int):
	"""For specific_info etc purposes, for storing sizes etc, so it can be formatted nicely
	But maybe this is unnecessary when pydantic is a requirement anyway and ByteSize is there"""

	def __str__(self) -> str:
		return format_byte_size(int(self))


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


class EmulationStatus(IntEnum):
	Good = 2
	Imperfect = 1
	Broken = 0
	Unknown = -1
