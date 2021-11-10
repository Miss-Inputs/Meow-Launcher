from abc import ABC, abstractproperty

class Runner(ABC):
	@property
	#Override this to show if something is not installed, etc
	def is_available(self) -> bool:
		return True

	@abstractproperty
	def name(self) -> str:
		pass
