#!/usr/bin/env python3

import subprocess
import os
import sys
import re
import time
import datetime
import shlex

import config
import launchers
from info import emulator_command_lines
from mame_helpers import get_mame_xml, get_full_name, get_mame_ui_config
from mame_metadata import add_metadata
from metadata import Metadata, SaveType

debug = '--debug' in sys.argv
print_times = '--print-times' in sys.argv

icon_line_regex = re.compile(r'^icons_directory\s+(.+)$')

def load_icons():
	d = {}
	for icon_directory in get_mame_ui_config().settings['icons_directory']:
		if os.path.isdir(icon_directory):
			for icon_file in os.listdir(icon_directory):
				name, ext = os.path.splitext(icon_file)
				if ext == '.ico': #Perhaps should have other formats?
					d[name] = os.path.join(icon_directory, icon_file)

	return d
icons = load_icons()

class Machine():
	def __init__(self, xml):
		self.xml = xml
		self.metadata = Metadata()
		self._add_metadata_fields()
		#This can't be an attribute because we might need to override it later! Bad Megan!
		self.name = self.xml.findtext('description')

	def _add_metadata_fields(self):
		self.metadata.specific_info['Source-File'] = self.source_file
		self.metadata.specific_info['Family-Basename'] = self.family
		self.metadata.specific_info['Family'] = get_full_name(self.family)

		self.metadata.year = self.xml.findtext('year')

		self.metadata.specific_info['Number-of-Players'] = self.number_of_players
		self.metadata.specific_info['Is-Mechanical'] = self.is_mechanical
		self.metadata.specific_info['Dispenses-Tickets'] = self.uses_device('ticket_dispenser')
		self.metadata.specific_info['Coin-Slots'] = self.input_element.attrib.get('coins', 0)

	@property
	def basename(self):
		return self.xml.attrib['name']

	@property
	def has_parent(self):
		return 'cloneof' in self.xml.attrib

	@property
	def parent(self):
		parent_name = self.xml.attrib.get('cloneof')
		if not parent_name:
			return None
		return Machine(get_mame_xml(parent_name).find('machine'))

	@property
	def family(self):
		return self.xml.attrib.get('cloneof', self.basename)

	@property
	def source_file(self):
		return os.path.splitext(self.xml.attrib['sourcefile'])[0]

	@property
	def icon(self):
		if not icons:
			return None

		basename_icon = icons.get(self.basename)
		if basename_icon:
			return basename_icon

		family_icon = icons.get(self.family)
		if family_icon:
			return family_icon

		return None

	def make_launcher(self):
		slot_options = {}
		if self.metadata.save_type == SaveType.MemoryCard and self.source_file == 'neogeo' and config.memcard_path:
			memory_card_path = os.path.join(config.memcard_path, self.basename + '.neo')
			if os.path.isfile(memory_card_path):
				slot_options['memc'] = shlex.quote(memory_card_path)

		command_line = emulator_command_lines.mame_command_line(self.basename, slot_options=slot_options)
		launchers.make_launcher(command_line, self.name, self.metadata, {'Type': 'MAME machine', 'Unique-ID': self.basename}, self.icon)

	@property
	def is_mechanical(self):
		return self.xml.attrib.get('ismechanical', 'no') == 'yes'

	@property
	def input_element(self):
		return self.xml.find('input')

	@property
	def number_of_players(self):
		return int(self.input_element.attrib.get('players', 0))

	@property
	def is_skeleton_driver(self):
		#Actually, we're making an educated guess here, as MACHINE_IS_SKELETON doesn't appear directly in the XML...
		#What I actually want to happen is to tell us if a machine will just display a blank screen and nothing else (because nobody wants those in a launcher). Right now that's not really possible without the false positives of games which don't have screens as such but they do display things via layouts (e.g. wackygtr) so the best we can do is say everything that doesn't have any kind of controls.
		return self.number_of_players == 0

	def uses_device(self, name):
		for device_ref in self.xml.findall('device_ref'):
			if device_ref.attrib['name'] == name:
				return True

		return False

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

def has_mandatory_slots(machine):
	for device in machine.xml.findall('device'):
		instance = device.find('instance')
		if instance is None:
			continue
		if device.attrib.get('mandatory', '0') == '1':
			return True
	return False

def process_machine(machine):
	if not should_process_machine(machine):
		return

	if not (machine.xml.find('softwarelist') is None) and machine.family not in config.okay_to_have_software:
		return

	if has_mandatory_slots(machine):
		if debug:
			print('%s (%s) has mandatory slots' % (machine.basename, machine.name))
		return

	if machine.is_skeleton_driver:
		#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
		#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up
		if debug:
			print('Skipping %s (%s) as it is probably a skeleton driver' % (machine.basename, machine.name))
		return

	add_metadata(machine)
	if config.exclude_non_arcade and machine.metadata.platform == 'Non-Arcade':
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

	if '--drivers' in sys.argv:
		arg_index = sys.argv.index('--drivers')
		if len(sys.argv) == 2:
			print('--drivers requires an argument')
			return

		driver_list = sys.argv[arg_index + 1].split(',')
		for driver_name in driver_list:
			process_driver(driver_name)
		return

	process_arcade()

if __name__ == '__main__':
	main()
