#!/usr/bin/env python3

import subprocess
import os
import sys
import re
import time
import datetime

import config
import launchers
from info import emulator_command_lines
from mame_helpers import get_mame_xml, get_full_name
from mame_metadata import add_input_info, add_metadata
from metadata import Metadata

debug = '--debug' in sys.argv
print_times = '--print-times' in sys.argv

icon_line_regex = re.compile(r'^icons_directory\s+(.+)$')
def get_icon_directories():
	ui_config_path = os.path.expanduser('~/.mame/ui.ini')
	if not os.path.isfile(ui_config_path):
		return None

	with open(ui_config_path, 'rt') as ui_config:
		for line in ui_config.readlines():
			icon_line_match = icon_line_regex.match(line)
			if icon_line_match:
				#I ain't about that relative path life fam
				return [dir for dir in icon_line_match[1].split(';') if dir.startswith('/')]

	return None

icon_directories = get_icon_directories()

def load_icons():
	d = {}
	for icon_directory in icon_directories:
		if os.path.isdir(icon_directory):
			for icon_file in os.listdir(icon_directory):
				name, ext = os.path.splitext(icon_file)
				if ext == '.ico':
					d[name] = os.path.join(icon_directory, icon_file)

	return d
icons = load_icons()

class Machine():
	def __init__(self, xml):
		self.xml = xml
		self.basename = xml.attrib['name']
		self.family = xml.attrib['cloneof'] if 'cloneof' in xml.attrib else self.basename
		self.name = xml.findtext('description')
		self.metadata = Metadata()

		self.source_file = os.path.splitext(xml.attrib['sourcefile'])[0]
		self.metadata.specific_info['Source-File'] = self.source_file

	def make_launcher(self):
		icon = None
		if icons:
			icon = icons.get(self.basename)
			if not icon:
				icon = icons.get(self.family)

		command_line = emulator_command_lines.mame_command_line(self.basename)
		launchers.make_launcher(command_line, self.name, self.metadata, {'Basename': self.basename}, icon)

def mame_verifyroms(basename):
	#FIXME Okay this is way too fuckin' slow
	try:
		subprocess.run(['mame', '-verifyroms', basename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
		return True
	except subprocess.CalledProcessError:
		return False

def should_process_machine(machine):
	if machine.xml.attrib['runnable'] == 'no':
		return False

	if machine.xml.attrib['isbios'] == 'yes':
		return False

	if machine.xml.attrib['isdevice'] == 'yes':
		return False

	return True

def process_machine(machine):
	if not should_process_machine(machine):
		return

	if not (machine.xml.find('softwarelist') is None) and machine.family not in config.okay_to_have_software:
		return

	machine.metadata.specific_info['Family-Basename'] = machine.family
	machine.metadata.specific_info['Family'] = get_full_name(machine.family)

	add_metadata(machine)
	if machine.metadata.specific_info.get('Probably-Skeleton-Driver', False):
		#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
		#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up
		if debug:
			print('Skipping %s (%s) as it is probably a skeleton driver' % (machine.basename, machine.name))
		return

	machine.make_launcher()

def get_mame_drivers():
	drivers = []

	process = subprocess.run(['mame', '-listsource'], stdout=subprocess.PIPE, universal_newlines=True)
	status = process.returncode
	output = process.stdout
	if status != 0:
		print('Shit')
		return []

	for line in output.splitlines():
		try:
			driver, source_file = line.split(None, 1)
			drivers.append((driver, os.path.splitext(source_file)[0]))
		except ValueError:
			print('For fucks sake ' + line)
			continue

	return drivers

def process_driver(driver):
	#You probably think this is why it's slow, right?  You think "Oh, that's silly, you're verifying every single romset
	#in existence before just getting the XML", that's what you're thinking, right?  Well, I am doing that, but as it
	#turns out if I do the verification inside process_machine it takes a whole lot longer.  I don't fully understand why
	#but I'll have you know I actually profiled it
	if not mame_verifyroms(driver):
		return

	xml = get_mame_xml(driver)
	if xml is None:
		return
	process_machine(Machine(xml.find('machine')))

def process_arcade():
	#Fuck iterparse by the way, if you stumble across this script and think "oh you should use iterparse instead of this
	#kludge!" you are wrong
	#(Okay, if you want an attempt at a reason why: I've tried it, and MAME's machine elements are actually more
	#complicated and seemingly refer to other machine elements that are displayed alongside the main one with an
	#individual -listxml)
	#Could it be faster to use -verifyroms globally and parse the output somehow and then get individual XML from
	#successful results?

	time_started = time.perf_counter()

	for driver, source_file in get_mame_drivers():
		if source_file in config.skipped_source_files:
			continue

		process_driver(driver)

	if print_times:
		time_ended = time.perf_counter()
		print('Arcade finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


def main():
	os.makedirs(config.output_folder, exist_ok=True)

	if sys.argv[1] == '--driver':
		process_driver(sys.argv[2])
		return

	process_arcade()

if __name__ == '__main__':
	main()
