from abc import ABC, abstractproperty

class Runner(ABC):
	@property
	#Override this to show if something is not installed, etc
	def is_available(self) -> bool:
		return True

	@abstractproperty
	def name(self) -> str:
		pass

	@property
	def is_emulated(self) -> bool:
		#Basically just decides if we should use the "Emulator" field or not
		return False