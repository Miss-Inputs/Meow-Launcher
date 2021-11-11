from abc import ABC, abstractmethod

from meowlauncher.metadata import Metadata

class Game(ABC):
	def __init__(self) -> None:
		self.metadata = Metadata()
	
	@property
	@abstractmethod
	def name(self) -> str:
		pass
