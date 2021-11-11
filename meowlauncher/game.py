from abc import ABC, abstractproperty

from meowlauncher.metadata import Metadata

class Game(ABC):
	def __init__(self) -> None:
		self.metadata = Metadata()
	
	@abstractproperty
	def name(self) -> str:
		pass
