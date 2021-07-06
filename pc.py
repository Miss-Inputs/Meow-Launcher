import datetime
import json
import os
import time
import traceback

import launchers
from common_paths import config_dir
from common_types import (EmulationNotSupportedException, MediaType,
                          NotARomException)
from config.emulator_config import emulator_configs
from config.main_config import main_config
from info.emulator_info import pc_emulators
from info.system_info import pc_systems
from metadata import Date, Metadata
from pc_common_metadata import fix_name


class App:
	def __init__(self, info):
		self.metadata = Metadata()
		self.info = info
		self.is_on_cd = info.get('is_on_cd', False)
		self.path = info['path']
		self.cd_path = None
		self.other_cd_paths = []
		if 'cd_path' in info:
			cd_paths = info['cd_path'] if isinstance(info['cd_path'], list) else [info['cd_path']]
			if self.base_folder:
				cd_paths = [os.path.join(self.base_folder, cd_path) for cd_path in cd_paths]
			self.cd_path = cd_paths[0]
			self.other_cd_paths = cd_paths[1:]
		elif self.is_on_cd:
			raise KeyError('cd_path is mandatory if is_on_cd is true')
		self.name = info.get('name', fix_name(self.get_fallback_name()))

	@property
	def base_folder(self):
		#Might want to override this in subclass, returns a folder on the host that might have other files related to the game (CD images, etc)
		#Return none if this is not relevant
		return os.path.dirname(self.path)

	def get_fallback_name(self):
		#Might want to override in subclass, maybe not - return something that should be used as the name if the user doesn't put any name in the config
		return os.path.basename(self.path)
	
	def get_launcher_id(self):
		#For overriding in subclass (but maybe this will do as a default), for Unique-ID in [X-Meow Launcher ID] section of launcher
		return self.path

	def add_metadata(self):
		self.metadata.media_type = MediaType.Executable
		if 'developer' in self.info:
			self.metadata.developer = self.info['developer']
		if 'publisher' in self.info:
			self.metadata.publisher = self.info['publisher']
		if 'year' in self.info:
			self.metadata.release_date = Date(self.info['year'])
		if 'category' in self.info:
			self.metadata.categories = [self.info['category']]
		if 'genre' in self.info:
			self.metadata.genre = self.info['genre']
		if 'subgenre' in self.info:
			self.metadata.subgenre = self.info['subgenre']
		if 'notes' in self.info:
			self.metadata.add_notes(self.info['notes'])
		self.additional_metadata()

	@property
	def is_valid(self):
		#To be overriden by subclass - return true if this config is pointing to something that actually exists
		return os.path.isfile(self.path)

	def additional_metadata(self):
		#To be overriden by subclass - optional, put any other platform-specific metadata you want in here
		pass

	def make_launcher(self, system_config):
		emulator_name = None
		params = None
		exception_reason = None
		for emulator in system_config.chosen_emulators:
			emulator_name = emulator
			if emulator_name not in pc_systems[system_config.name].emulators:
				if main_config.debug:
					print(emulator_name, 'is not a valid emulator for', system_config.name)
				continue
			emulator_config = emulator_configs[emulator]
			try:
				if 'compat' in self.info:
					if not self.info['compat'].get(emulator, True):
						raise EmulationNotSupportedException('Apparently not supported')
				params = pc_emulators[emulator].get_launch_params(self, system_config, emulator_config)
				if params:
					break
			except (EmulationNotSupportedException, NotARomException) as ex:
				exception_reason = ex

		if not params:
			if main_config.debug:
				print(self.path, 'could not be launched by', system_config.chosen_emulators, 'because', exception_reason)
			return

		self.metadata.emulator_name = emulator_name
		launchers.make_launcher(params, self.name, self.metadata, system_config.name, self.get_launcher_id())

def process_app(app_info, app_class, system_config):
	app = app_class(app_info)
	try:
		if not app.is_valid:
			print('Skipping', app.name, app.path, 'config is not valid')
			return
		app.metadata.platform = system_config.name
		app.add_metadata()
		app.make_launcher(system_config)
	except Exception as ex: #pylint: disable=broad-except
		print('Ah bugger', app.path, app.name, ex, type(ex), traceback.extract_tb(ex.__traceback__)[1:])

def make_launchers(platform, app_class, system_config):
	time_started = time.perf_counter()

	app_list_path = os.path.join(config_dir, pc_systems[platform].json_name + '.json')
	try:
		with open(app_list_path, 'rt') as f:
			app_list = json.load(f)
			for app in app_list:
				try:
					process_app(app, app_class, system_config)
				except KeyError as ke:
					print(app_list_path, app.get('name', 'unknown entry'), ': Missing needed key', ke)
	except json.JSONDecodeError as json_fuckin_bloody_error:
		print(app_list_path, 'is borked, skipping', platform, json_fuckin_bloody_error)
	except FileNotFoundError:
		return

	if main_config.print_times:
		time_ended = time.perf_counter()
		print(platform, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
