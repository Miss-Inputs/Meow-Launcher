import datetime
import json
import os
import time
import traceback
from typing import Any, Optional, Type

from meowlauncher.common_paths import config_dir
from meowlauncher.common_types import (EmulationNotSupportedException,
                                       NotARomException)
from meowlauncher.config.emulator_config import emulator_configs
from meowlauncher.config.main_config import main_config
from meowlauncher.config.system_config import PlatformConfig
from meowlauncher.data.emulated_platforms import pc_platforms
from meowlauncher.data.emulators import pc_emulators
from meowlauncher.desktop_launchers import make_linux_desktop_for_launcher
from meowlauncher.games.pc import App, AppLauncher


def get_launcher(app: App, launcher_type: Type[AppLauncher], platform_config: PlatformConfig) -> Optional[AppLauncher]:
	emulator = None
	exception_reason = None
	for potential_emulator_name in platform_config.chosen_emulators:
		emulator_name = potential_emulator_name
		if emulator_name not in pc_platforms[platform_config.name].emulators:
			if main_config.debug:
				print(emulator_name, 'is not a valid emulator for', platform_config.name)
			continue
		emulator_config = emulator_configs[potential_emulator_name]
		try:
			if 'compat' in app.info:
				if not app.info['compat'].get(potential_emulator_name, True):
					raise EmulationNotSupportedException('Apparently not supported')
			params = pc_emulators[potential_emulator_name].get_launch_params(app, platform_config.options, emulator_config)
			if params:
				emulator = pc_emulators[potential_emulator_name]
				break
		except (EmulationNotSupportedException, NotARomException) as ex:
			exception_reason = ex

	if not emulator:
		if main_config.debug:
			print(app.path, 'could not be launched by', platform_config.chosen_emulators, 'because', exception_reason)
		return None

	return launcher_type(app, emulator, platform_config, emulator_config)

def process_app(app_info: dict[str, Any], app_class: Type[App], launcher_class: Type[AppLauncher], platform_config: PlatformConfig) -> None:
	app = app_class(app_info)
	try:
		if not app.is_valid:
			print('Skipping', app.name, app.path, 'config is not valid')
			return
		app.metadata.platform = platform_config.name #TODO This logic shouldn't be here
		app.add_metadata()
		#app.make_launcher(platform_config)
		launcher = get_launcher(app, launcher_class, platform_config)
		if launcher:
			make_linux_desktop_for_launcher(launcher)

	except Exception as ex: #pylint: disable=broad-except
		print('Ah bugger', app.path, app.name, ex, type(ex), traceback.extract_tb(ex.__traceback__)[1:])

def make_launchers(platform: str, app_class: Type[App], launcher_class: Type[AppLauncher], platform_config: PlatformConfig) -> None:
	time_started = time.perf_counter()

	app_list_path = os.path.join(config_dir, pc_platforms[platform].json_name + '.json')
	try:
		with open(app_list_path, 'rt') as f:
			app_list = json.load(f)
			for app in app_list:
				try:
					process_app(app, app_class, launcher_class, platform_config)
				except KeyError as ke:
					print(app_list_path, app.get('name', 'unknown entry'), ': Missing needed key', ke)
	except json.JSONDecodeError as json_fuckin_bloody_error:
		print(app_list_path, 'is borked, skipping', platform, json_fuckin_bloody_error)
	except FileNotFoundError:
		return

	if main_config.print_times:
		time_ended = time.perf_counter()
		print(platform, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
