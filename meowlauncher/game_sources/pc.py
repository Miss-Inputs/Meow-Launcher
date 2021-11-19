import json
import traceback
from abc import ABC
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Optional

from meowlauncher.common_paths import config_dir
from meowlauncher.common_types import (EmulationNotSupportedException,
                                       NotARomException)
from meowlauncher.config.emulator_config import emulator_configs
from meowlauncher.config.main_config import main_config
from meowlauncher.config.platform_config import platform_configs
from meowlauncher.configured_emulator import ConfiguredEmulator
from meowlauncher.data.emulated_platforms import pc_platforms
from meowlauncher.data.emulators import pc_emulators
from meowlauncher.emulated_platform import PCPlatform
from meowlauncher.emulator import PCEmulator
from meowlauncher.game_source import ChooseableEmulatorGameSource
from meowlauncher.games.pc import App, AppLauncher


class PCGameSource(ChooseableEmulatorGameSource[PCEmulator], ABC):
	#Leave no_longer_exists to the subclasses as they may like to have custom logic

	def __init__(self, platform_name: str, app_type: type[App], launcher_type: type[AppLauncher]) -> None:
		self.platform: PCPlatform = pc_platforms[platform_name]
		self._app_type = app_type
		self._launcher_type = launcher_type
		platform_config = platform_configs.get(platform_name)
		if not platform_config:
			self._is_available = False
			return
		super().__init__(platform_config, self.platform, pc_emulators)

		self._app_list_path = config_dir.joinpath(self.platform.json_name + '.json')
		self._app_list: Optional[Sequence[Mapping[str, Any]]] = None
		try:
			self._is_available = bool(platform_config.chosen_emulators)
			with self._app_list_path.open('rt', encoding='utf-8') as f:
				self._app_list = json.load(f)
		except json.JSONDecodeError as json_fuckin_bloody_error:
			print(self._app_list_path, 'is borked, skipping', platform_name, json_fuckin_bloody_error)
			self._is_available = False
		except FileNotFoundError:
			self._is_available = False

	@property
	def name(self) -> str:
		return self.platform.name

	@property
	def is_available(self) -> bool:
		return self._is_available

	def _get_launcher(self, app: App) -> Optional[AppLauncher]:
		if not self.platform_config:
			raise AssertionError('Should have checked is_available already, platform_config is None')

		emulator: Optional[ConfiguredEmulator] = None
		exception_reason = None
		for chosen_emulator in self.get_chosen_emulators():
			emulator_config = emulator_configs[chosen_emulator.config_name]
			try:
				if 'compat' in app.info:
					if not app.info['compat'].get(chosen_emulator.config_name, True):
						raise EmulationNotSupportedException('Apparently not supported')
				potential_emulator = ConfiguredEmulator(chosen_emulator, emulator_config)
				command = potential_emulator.get_launch_command_for_game(app, self.platform_config.options)
				if command:
					emulator = potential_emulator
					break
			except (EmulationNotSupportedException, NotARomException) as ex:
				exception_reason = ex

		if not emulator:
			if main_config.debug:
				print(app.path, 'could not be launched by', self.platform_config.chosen_emulators, 'because', exception_reason)
			return None

		return self._launcher_type(app, emulator, self.platform_config)

	def _process_app(self, app_info: Mapping[str, Any]) -> Optional[AppLauncher]:
		if not self.platform_config:
			raise AssertionError('Should have checked is_available already, platform_config is None')
		app = self._app_type(app_info, self.platform_config)
		try:
			if not app.is_valid:
				print('Skipping', app.name, app.path, 'config is not valid')
				return None
			app.metadata.platform = self.platform.name #TODO This logic shouldn't be here I think
			app.add_metadata()
			return self._get_launcher(app)
			
		except Exception as ex: #pylint: disable=broad-except
			print('Ah bugger', app.path, app.name, ex, type(ex), traceback.extract_tb(ex.__traceback__)[1:])
			return None

	#Return value here could be a generic type value I suppose, if you were into that sort of thing
	def get_launchers(self) -> Iterable[AppLauncher]:
		if not self._app_list:
			raise AssertionError('PCGameSource.get_launchers should not be called without checking .is_available()')
		for app in self._app_list:
			try:
				launcher = self._process_app(app)
				if launcher:
					yield launcher
			except KeyError as ke:
				print(self._app_list_path, app.get('name', 'unknown entry'), ': Missing needed key', ke)
				continue
