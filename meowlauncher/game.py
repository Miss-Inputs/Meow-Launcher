from abc import ABC, abstractproperty

class Game(ABC):
	
	@abstractproperty
	def name(self) -> str:
		pass
