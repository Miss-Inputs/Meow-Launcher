import json
import logging
from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from meowlauncher.common_paths import config_dir
from meowlauncher.settings.emulator_config import emulator_configs
from meowlauncher.settings.platform_config import platform_configs
from meowlauncher.configured_emulator import ConfiguredEmulator
from meowlauncher.data.emulated_platforms import manually_specified_platforms
from meowlauncher.exceptions import (
	EmulationNotSupportedException,
	NotActuallyLaunchableGameException,
)
from meowlauncher.game_source import ChooseableEmulatorGameSource
from meowlauncher.manually_specified_game import ManuallySpecifiedGame, ManuallySpecifiedLauncher

if TYPE_CHECKING:
	from collections.abc import Iterator, Mapping, Sequence

	from .emulator import Emulator

logger = logging.getLogger(__name__)

ManuallySpecifiedGameType_co = TypeVar('ManuallySpecifiedGameType_co', bound=ManuallySpecifiedGame, covariant=True)
class ManuallySpecifiedGameSource(ChooseableEmulatorGameSource['Emulator[ManuallySpecifiedGameType_co]'], ABC, Generic[ManuallySpecifiedGameType_co]):
	"""Base class for game sources where the user specifies which games exist manually, usually out of necessity (or impracticality of automatic scanning, or ultimately just inaccuracy) because that kind of sucks, e.g. DOS games where you _could_ theoretically create launchers for every executable but for now we just get the user to tell us which games exist with which executable
	
	TODO: This shouldn't necessarily subclass ChooseableEmulatorGameSource
	TODO: Leave no_longer_exists to the subclasses as they may like to have custom logic
	TODO: A lot of __init__ should be in __new__ instead I think (self.platform should be cls.platform probably, and then GameSource.name can use it)"""

	def __init__(self, platform_name: str, app_type: type[ManuallySpecifiedGameType_co], launcher_type: type[ManuallySpecifiedLauncher], emulators_dict: 'Mapping[str, Emulator[ManuallySpecifiedGameType_co]]') -> None:
		self.platform = manually_specified_platforms[platform_name] #TODO: Might not always be a thing
		self._app_type = app_type
		self._launcher_type = launcher_type
		platform_config = platform_configs.get(platform_name)
		if not platform_config:
			self._is_available = False
			return
		super().__init__(platform_config, self.platform, emulators_dict)

		self._app_list_path = config_dir.joinpath(self.platform.json_name + '.json')
		self._app_list: 'Sequence[Mapping[str, Any]] | None' = None
		try:
			self._is_available = bool(platform_config.chosen_emulators)
			self._app_list = json.loads(self._app_list_path.read_bytes())
		except json.JSONDecodeError:
			logger.exception('%s is borked, skipping %s', self._app_list_path, platform_name)
			self._is_available = False
		except FileNotFoundError:
			self._is_available = False

	@property
	def is_available(self) -> bool:
		return self._is_available

	def _get_launcher(self, app: ManuallySpecifiedGame) -> ManuallySpecifiedLauncher | None:
		emulator: ConfiguredEmulator | None = None
		exception_reason = None
		for chosen_emulator in self.iter_chosen_emulators():
			emulator_config = emulator_configs[chosen_emulator.config_name]
			try:
				if 'compat' in app.json:
					if not app.json['compat'].get(chosen_emulator.config_name, True):
						raise EmulationNotSupportedException('Apparently not supported')
				potential_emulator = ConfiguredEmulator(chosen_emulator, emulator_config)
				#TODO: This doesn't seem right… why are we just throwing away the result here
				potential_emulator.get_launch_command_for_game(app, self.platform_config.options)
				emulator = potential_emulator
				break
			except (EmulationNotSupportedException, NotActuallyLaunchableGameException) as ex:
				exception_reason = ex

		if not emulator:
			if isinstance(exception_reason, EmulationNotSupportedException):
				logger.warning('%s could not be launched by %s', app, self.platform_config.chosen_emulators, exc_info=exception_reason)
			else:
				logger.debug('%s could not be launched by %s', app, self.platform_config.chosen_emulators, exc_info=exception_reason)
			return None

		return self._launcher_type(app, emulator, self.platform_config)

	def _process_app(self, app_info: 'Mapping[str, Any]') -> ManuallySpecifiedLauncher | None:
		app = self._app_type(app_info, self.platform_config)
		try:
			if not app.is_valid:
				logger.warning('Skipping %s as config is not valid', app)
				return None
			app.add_info()
			return self._get_launcher(app)
			
		except Exception: #pylint: disable=broad-except
			logger.exception('Ah bugger %s had an error', app)
			return None

	def iter_launchers(self) -> 'Iterator[ManuallySpecifiedLauncher]':
		assert self._app_list is not None, '_app_list is None, ManuallySpecifiedGameSource.get_launchers should not be called without checking .is_available()'
		for app in self._app_list:
			try:
				launcher = self._process_app(app)
				if launcher:
					yield launcher
			except KeyError as ke:
				logger.exception('%s is missing needed key %s in %s', self._app_list_path, ke.args, app.get('name', 'unknown entry'))
				continue

	def no_longer_exists(self, game_id: str) -> bool:
		"""Uses the same path or cd_path:path scheme as the default ManuallySpecifiedLauncher"""
		path = game_id.partition(':')[0]
		return not Path(path).exists()
