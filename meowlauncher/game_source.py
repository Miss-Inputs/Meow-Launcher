from abc import ABC, abstractmethod
from collections.abc import Iterable

from meowlauncher.launcher import Launcher

class GameSource(ABC):
	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@property
	def description(self) -> str:
		return f'{self.name} games'

	@property
	@abstractmethod
	def is_available(self) -> bool:
		pass

	@abstractmethod
	def no_longer_exists(self, game_id: str) -> bool:
		pass

	#TODO: Should have has_been_done somewhere in here? Maybe

	@abstractmethod
	def get_launchers(self) -> Iterable[Launcher]:
		pass
