
class NotLaunchableException(Exception):
	"""Base class for all "could or should not make launcher for this game for whatever funny reason" exceptions"""

class GameNotSupportedException(NotLaunchableException):
	"""Game is not playable for one reason or another, but actually is a game (or other software, for you nitpickers out there)"""

class EmulationNotSupportedException(GameNotSupportedException):
	"""When a particular emulator does not support this game"""

class ExtensionNotSupportedException(EmulationNotSupportedException):
	"""Particular emulator does not support this file extension (maybe should be "file type" instead of extension to be more generic)"""

class NotActuallyLaunchableGameException(NotLaunchableException):
	"""Game is not something that can be launched at all"""
