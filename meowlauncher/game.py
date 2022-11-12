from abc import ABC, abstractmethod

from meowlauncher.info import GameInfo

class Game(ABC):
	def __init__(self) -> None:
		self.info = GameInfo()
	
	@property
	@abstractmethod
	def name(self) -> str:
		pass
