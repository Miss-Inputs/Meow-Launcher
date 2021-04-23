import datetime
import json
import os
import time

import launchers
from common_paths import config_dir
from common_types import (EmulationNotSupportedException, MediaType,
                          NotARomException)
from config.main_config import main_config
from metadata import Date, Metadata


class App:
	def __init__(self, info):
		self.metadata = Metadata()
		self.info = info
		self.path = info['path']
		self.name = info.get('name', self.get_fallback_name())

	@property
	def platform_name(self):
		#Intended to be overridden by subclass
		return 'PC'

	def get_fallback_name(self):
		#Might want to override in subclass, maybe not
		return os.path.basename(self.path)
	
	def get_launcher_id(self):
		#Might want to override in subclass, maybe not
		return self.path

	def add_metadata(self):
		self.metadata.platform = self.platform_name
		self.additional_metadata()
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
			self.metadata.notes = self.info['notes']
		
		# self.languages = []
		# self.save_type = SaveType.Unknown
		# self.product_code = None
		# self.regions = []
		# self.media_type = None
		# self.disc_number = None
		# self.disc_total = None
		# self.series = None
		# self.series_index = None
		#Maybe?

	@property
	def is_valid(self):
		#To be overriden by subclass
		return True

	def additional_metadata(self):
		#To be overriden by subclass
		pass

	def make_launcher(self, emulator_list, config):
		emulator_name = None
		params = None
		exception_reason = None
		for emulator in config.chosen_emulators:
			emulator_name = emulator
			try:
				params = emulator_list[emulator].get_launch_params(self, config.options)
				if params:
					break
			except (EmulationNotSupportedException, NotARomException) as ex:
				exception_reason = ex

		if not params:
			if main_config.debug:
				print(self.path, 'could not be launched by', config.chosen_emulators, 'because', exception_reason)
			return

		self.metadata.emulator_name = emulator_name
		launchers.make_launcher(params, self.name, self.metadata, self.platform_name, self.get_launcher_id())

def process_app(app_info, app_class, emulator_list, config):
	app = app_class(app_info)
	#try:
	if not app.is_valid:
		print('Skipping', app.name, app.path, 'config is not valid')
		return
	app.add_metadata()
	app.make_launcher(emulator_list, config)
	#except Exception as ex: #pylint: disable=broad-except
	#	print('Ah bugger', app.path, app.name, ex, type(ex))

def make_launchers(platform, app_class, emulator_list, config):
	time_started = time.perf_counter()

	app_list_path = os.path.join(config_dir, platform.lower() + '.json')
	try:
		with open(app_list_path, 'rt') as f:
			app_list = json.load(f)
			for app in app_list:
				try:
					process_app(app, app_class, emulator_list, config)
				except KeyError:
					print(app_list_path, 'has unknown entry that is missing needed keys (path, name)')
	except json.JSONDecodeError as json_fuckin_bloody_error:
		print(app_list_path, 'is borked, skipping', platform, json_fuckin_bloody_error)
	except FileNotFoundError:
		return

	if main_config.print_times:
		time_ended = time.perf_counter()
		print(platform, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
