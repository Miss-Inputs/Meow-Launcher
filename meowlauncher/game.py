from abc import ABC, abstractmethod

from meowlauncher.info import GameInfo

class Game(ABC):
	"""Base class for Game, whatever it really does by itself, I dunno
	Whoops!
	Well theoretically it represents a game that has been scanned and found, holds info, but we don't know if we can launch it or not yet, as this class doesn't do that"""
	def __init__(self) -> None:
		self.info = GameInfo()
	
	@property
	@abstractmethod
	def name(self) -> str:
		pass

__doc__ = Game.__doc__ or Game.__name__
