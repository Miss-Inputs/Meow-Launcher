import datetime
import json
import os
import time

import config.main_config
import config.system_config
from common_paths import config_dir
from common_types import MediaType
from metadata import Metadata

conf = config.main_config.main_config
system_configs = config.system_config.system_configs

class App:
	def __init__(self, info):
		self.metadata = Metadata()
		self.info = info
		self.path = info['path']
		self.name = info['name']
		self.add_metadata()

	def add_metadata(self):
		self.additional_metadata()
		self.metadata.media_type = MediaType.Executable

		if 'developer' in self.info:
			self.metadata.developer = self.info['developer']
		if 'publisher' in self.info:
			self.metadata.publisher = self.info['publisher']
		if 'year' in self.info:
			self.metadata.year = self.info['year']
		if 'category' in self.info:
			self.metadata.categories = [self.info['category']]
		if 'genre' in self.info:
			self.metadata.genre = self.info['genre']
		if 'subgenre' in self.info:
			self.metadata.subgenre = self.info['subgenre']
		if 'is_adult' in self.info:
			self.metadata.nsfw = self.info['is_adult']
		if 'notes' in self.info:
			self.metadata.notes = self.info['notes']
		#Could put anything here, really

	def additional_metadata(self):
		#To be overriden by subclass
		pass

	def make_launcher(self):
		#To be overriden by subclass
		pass

def process_app(app_info, app_class):
	app = app_class(app_info)
	app.make_launcher()

def make_launchers(platform, app_class):
	system_config = system_configs[platform]
	if not system_config:
		return
	if not system_config.chosen_emulators:
		return

	time_started = time.perf_counter()

	app_list_path = os.path.join(config_dir, platform.lower() + '.json')
	try:
		with open(app_list_path, 'rt') as f:
			app_list = json.load(f)
			for app in app_list:
				try:
					process_app(app, app_class)
				except KeyError:
					print(app_list_path, 'has unknown entry that is missing needed keys (path, name)')
	except json.JSONDecodeError:
		print(app_list_path, 'is borked, skipping', platform)
	except FileNotFoundError:
		return

	if conf.print_times:
		time_ended = time.perf_counter()
		print(platform, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
