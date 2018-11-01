#!/usr/bin/env python3

import subprocess
import os
import sys
import re
import time
import datetime
import shlex

import launchers
from info import emulator_command_lines
from config import main_config
from mame_helpers import get_mame_xml, get_full_name, get_mame_ui_config, consistentify_manufacturer
from mame_metadata import add_metadata
from metadata import Metadata, SaveType

debug = '--debug' in sys.argv
print_times = '--print-times' in sys.argv

icon_line_regex = re.compile(r'^icons_directory\s+(.+)$')

def load_icons():
	d = {}
	mame_ui_config = get_mame_ui_config()
	for icon_directory in mame_ui_config.settings.get('icons_directory', []):
		if os.path.isdir(icon_directory):
			for icon_file in os.listdir(icon_directory):
				name, ext = os.path.splitext(icon_file)
				if ext == '.ico': #Perhaps should have other formats?
					d[name] = os.path.join(icon_directory, icon_file)

	return d
icons = load_icons()

licensed_arcade_game_regex = re.compile(r'^(.+?) \((.+?) license\)$')
licensed_from_regex = re.compile(r'^(.+?) \(licensed from (.+?)\)$')
hack_regex = re.compile(r'^hack \((.+)\)$')

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
		self.metadata.specific_info['Requires-CHD'] = self.requires_chds
		self.metadata.specific_info['Romless'] = self.romless
		self.metadata.specific_info['BIOS-Used'] = self.bios

		self._add_manufacturer()

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
		if self.metadata.save_type == SaveType.MemoryCard and self.source_file == 'neogeo' and main_config.memcard_path:
			memory_card_path = os.path.join(main_config.memcard_path, self.basename + '.neo')
			if os.path.isfile(memory_card_path):
				slot_options['memc'] = shlex.quote(memory_card_path)
			else:
				memory_card_path = os.path.join(main_config.memcard_path, self.family + '.neo')
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

	@property
	def requires_chds(self):
		#Hmm... should this include where all <disk> has status == "nodump"? e.g. Dragon's Lair has no CHD dump, would it be useful to say that it requires CHDs because it's supposed to have one but doesn't, or not, because you have a good romset without one
		#I guess I should have a look at how the MAME inbuilt UI does this
		return self.xml.find('disk') is not None

	@property
	def romless(self):
		if self.requires_chds:
			return False
		if self.xml.find('rom') is None:
			return True

		for rom in self.xml.findall('rom'):
			if rom.attrib.get('status', 'good') != 'nodump':
				return False

		return True

	@property
	def bios(self):
		romof = self.xml.attrib.get('romof')
		if self.has_parent and romof == self.family:
			return self.parent.bios
		return romof

	def _add_manufacturer(self):
		manufacturer = self.xml.findtext('manufacturer')
		license_match = licensed_arcade_game_regex.fullmatch(manufacturer)
		licensed_from_match = licensed_from_regex.fullmatch(manufacturer)
		hack_match = hack_regex.fullmatch(manufacturer)
		if license_match:
			developer = license_match[1]
			publisher = license_match[2]
		elif licensed_from_match:
			developer = manufacturer
			publisher = licensed_from_match[1]
			self.metadata.specific_info['Licensed-From'] = licensed_from_match[2]
		else:
			if not manufacturer.startswith(('bootleg', 'hack')):
				#TODO: Not always correct in cases where manufacturer is formatted as "Developer / Publisher", but then it never was correct, so it's just less not correct, which is fine
				developer = manufacturer
				publisher = manufacturer
			elif self.has_parent:
				if hack_match:
					self.metadata.specific_info['Hacked-By'] = hack_match[1]
				developer = self.parent.metadata.developer
				publisher = self.parent.metadata.publisher
			else:
				developer = None #It'd be the original not-bootleg game's developer but we can't get that programmatically without a parent etc
				publisher = manufacturer
		self.metadata.developer = consistentify_manufacturer(developer)
		self.metadata.publisher = consistentify_manufacturer(publisher)

def mame_verifyroms(basename):
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


#Normally, we'd skip over anything that has software because that indicates it's a system you plug games into and not
#usable by itself.  But these are things that are really just standalone things, but they have an expansion for
#whatever reason and are actually fine
#cfa3000 is kinda fine but it counts as a BBC Micro so it counts as not fine, due to detecting this stuff by
#parent/clone family
okay_to_have_software = ['vii', 'snspell', 'tntell']

def process_machine(machine):
	if not should_process_machine(machine):
		return

	if not (machine.xml.find('softwarelist') is None) and machine.family not in okay_to_have_software:
		return

	if has_mandatory_slots(machine):
		if debug:
			print('%s (%s, %s) has mandatory slots' % (machine.name, machine.basename, machine.source_file))
		return

	if machine.is_skeleton_driver:
		#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
		#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up
		if debug:
			print('Skipping %s (%s, %s) as it is probably a skeleton driver' % (machine.name, machine.basename, machine.source_file))
		return

	add_metadata(machine)
	if main_config.exclude_non_arcade and machine.metadata.platform == 'Non-Arcade':
		return
	if main_config.exclude_pinball and machine.metadata.platform == 'Pinball':
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

	#You hear that, myself? Stop trying to do mame_verifyroms later! It will go from taking 1 hour to taking 3 and a half hours! Stop it!
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
		if source_file in main_config.skipped_source_files:
			continue

		process_driver(driver)

	if print_times:
		time_ended = time.perf_counter()
		print('Arcade finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


def main():
	#os.makedirs(main_config.output_folder, exist_ok=True)

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
