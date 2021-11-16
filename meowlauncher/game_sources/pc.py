import json
import os
import traceback
from abc import ABC
from collections.abc import Iterable, Mapping
from typing import Any, Optional

from meowlauncher.common_paths import config_dir
from meowlauncher.common_types import (EmulationNotSupportedException,
                                       NotARomException)
from meowlauncher.config.emulator_config import emulator_configs
from meowlauncher.config.main_config import main_config
from meowlauncher.config.platform_config import PlatformConfig
from meowlauncher.configured_emulator import ConfiguredEmulator
from meowlauncher.data.emulated_platforms import pc_platforms
from meowlauncher.data.emulators import pc_emulators
from meowlauncher.game_source import GameSource
from meowlauncher.games.pc import App, AppLauncher


class PCGameSource(GameSource, ABC):
	#Leave no_longer_exists to the subclasses as they may like to have custom logic

	def __init__(self, platform: str, app_type: type[App], launcher_type: type[AppLauncher], platform_config: Optional[PlatformConfig]) -> None:
		self.platform = platform
		self.app_type = app_type
		self.launcher_type = launcher_type
		self.platform_config = platform_config
		if not platform_config:
			self._is_available = False
			return

		self._app_list_path = os.path.join(config_dir, pc_platforms[self.platform].json_name + '.json')
		try:
			self._is_available = bool(platform_config.chosen_emulators)
			with open(self._app_list_path, 'rt', encoding='utf-8') as f:
				self._app_list = json.load(f)
		except json.JSONDecodeError as json_fuckin_bloody_error:
			print(self._app_list_path, 'is borked, skipping', platform, json_fuckin_bloody_error)
			self._is_available = False
		except FileNotFoundError:
			self._is_available = False

	@property
	def name(self) -> str:
		return self.platform

	@property
	def is_available(self) -> bool:
		return self._is_available

	def _get_launcher(self, app: App) -> Optional[AppLauncher]:
		if not self.platform_config:
			raise AssertionError('Should have checked is_available already, platform_config is None')

		emulator = None
		exception_reason = None
		for potential_emulator_name in self.platform_config.chosen_emulators:
			emulator_name = potential_emulator_name
			if emulator_name not in pc_platforms[self.platform_config.name].emulators:
				if main_config.debug:
					print(emulator_name, 'is not a valid emulator for', self.platform_config.name)
				continue
			emulator_config = emulator_configs[potential_emulator_name]
			try:
				if 'compat' in app.info:
					if not app.info['compat'].get(potential_emulator_name, True):
						raise EmulationNotSupportedException('Apparently not supported')
				potential_emulator = ConfiguredEmulator(pc_emulators[potential_emulator_name], emulator_config)
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

		return self.launcher_type(app, emulator, self.platform_config)

	def _process_app(self, app_info: Mapping[str, Any]) -> Optional[AppLauncher]:
		if not self.platform_config:
			raise AssertionError('Should have checked is_available already, platform_config is None')
		app = self.app_type(app_info, self.platform_config)
		try:
			if not app.is_valid:
				print('Skipping', app.name, app.path, 'config is not valid')
				return None
			app.metadata.platform = self.platform #TODO This logic shouldn't be here I think
			app.add_metadata()
			return self._get_launcher(app)
			
		except Exception as ex: #pylint: disable=broad-except
			print('Ah bugger', app.path, app.name, ex, type(ex), traceback.extract_tb(ex.__traceback__)[1:])
			return None

	def get_launchers(self) -> Iterable[AppLauncher]:
		for app in self._app_list:
			try:
				launcher = self._process_app(app)
				if launcher:
					yield launcher
			except KeyError as ke:
				print(self._app_list_path, app.get('name', 'unknown entry'), ': Missing needed key', ke)
				continue
