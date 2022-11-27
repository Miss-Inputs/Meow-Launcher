from enum import Enum

__doc__ = """Various enums etc for MAME shared between machine XMLs and software lists because I couldn't decide where else to put them"""

class ROMLoadFlag(Enum):
	"""Values for "loadflag" attribute in MAME -listxml or software lists
	See also https://github.com/mamedev/mame/blob/master/src/emu/xmlentry.h#L30
	"""
	Load16Byte = "load16_byte"
	Load16Word = "load16_word"
	Load16Wordswap = "load16_word_swap"
	Load32Byte = "load32_byte"
	Load32Word = "load32_word"
	Load32WordSwap = "load32_word_swap"
	Load32DoubleWord = "load32_dword"
	Load64Word = "load64_word"
	Load64WordSwap = "load64_word_swap"
	Reload = "reload"
	"""Load the same ROM from the last position, which is why we need this to be a Sequence"""
	Fill = "fill"
	"""Requires the value attribute to be present, means this ROM is one byte repeated"""
	Continue = "continue"
	"""Continues loading the previous ROM, which implies it was bigger than the given size… oh dear that's complicated"""
	ReloadPlain = "reload_plain"
	"""Load the same ROM from the last position, which is why we need this to be a Sequence, but don't inherit the flags"""
	Ignore = "ignore"

class ROMStatus(Enum):
	"""Values for "status" attribute in MAME -listxml or software lists"""
	Good = 'good'
	BadDump = 'baddump'
	NoDump = 'nodump'

