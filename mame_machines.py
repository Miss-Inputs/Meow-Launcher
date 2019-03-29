#!/usr/bin/env python3

import subprocess
import os
import sys
import re
import time
import datetime

import launchers
from info import emulator_command_lines
from config import main_config
from mame_helpers import get_mame_xml, consistentify_manufacturer, iter_mame_entire_xml, get_icons
from mame_metadata import add_metadata
from metadata import Metadata, EmulationStatus
from common_types import SaveType

debug = '--debug' in sys.argv

icon_line_regex = re.compile(r'^icons_directory\s+(.+)$')

licensed_arcade_game_regex = re.compile(r'^(.+?) \((.+?) license\)$')
licensed_from_regex = re.compile(r'^(.+?) \(licensed from (.+?)\)$')
hack_regex = re.compile(r'^hack \((.+)\)$')

class Machine():
	def __init__(self, xml, init_metadata=False):
		self.xml = xml
		#This can't be an attribute because we might need to override it later! Bad Megan!
		self.name = self.xml.findtext('description')
		self.metadata = Metadata()
		self._has_inited_metadata = False
		if init_metadata:
			self._add_metadata_fields()

	def _add_metadata_fields(self):
		self._has_inited_metadata = True
		self.metadata.specific_info['Source-File'] = self.source_file
		self.metadata.specific_info['Family-Basename'] = self.family
		self.metadata.specific_info['Family'] = self.family_name

		self.metadata.year = self.xml.findtext('year')

		self.metadata.specific_info['Number-of-Players'] = self.number_of_players
		self.metadata.specific_info['Is-Mechanical'] = self.is_mechanical
		self.metadata.specific_info['Dispenses-Tickets'] = self.uses_device('ticket_dispenser')
		self.metadata.specific_info['Coin-Slots'] = self.input_element.attrib.get('coins', 0) if self.input_element is not None else 0
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
		return Machine(get_mame_xml(parent_name), True)

	@property
	def family(self):
		return self.xml.attrib.get('cloneof', self.basename)

	@property
	def family_name(self):
		return self.parent.name if self.has_parent else self.name

	@property
	def source_file(self):
		return os.path.splitext(self.xml.attrib['sourcefile'])[0]

	@property
	def icon(self):
		icons = get_icons()
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
		if not self._has_inited_metadata:
			self._add_metadata_fields()

		slot_options = {}
		if self.metadata.save_type == SaveType.MemoryCard and self.source_file == 'neogeo' and main_config.memcard_path:
			memory_card_path = os.path.join(main_config.memcard_path, self.basename + '.neo')
			if os.path.isfile(memory_card_path):
				slot_options['memc'] = memory_card_path
			else:
				memory_card_path = os.path.join(main_config.memcard_path, self.family + '.neo')
				if os.path.isfile(memory_card_path):
					slot_options['memc'] = memory_card_path

		exe_args = emulator_command_lines.mame_command_line(self.basename, slot_options=slot_options)
		launchers.make_launcher('mame', exe_args, self.name, self.metadata, 'MAME machine', self.basename, self.icon)

	@property
	def is_mechanical(self):
		return self.xml.attrib.get('ismechanical', 'no') == 'yes'

	@property
	def input_element(self):
		return self.xml.find('input')

	@property
	def number_of_players(self):
		if self.input_element is None:
			#This would happen if we ended up loading a device or whatever, so let's not crash the whole dang program. Also, since you can't play a device, they have 0 players. But they won't have launchers anyway, this is just to stop the NoneType explosion.
			return 0
		return int(self.input_element.attrib.get('players', 0))

	@property
	def driver_element(self):
		return self.xml.find('driver')

	@property
	def overall_status(self):
		if not driver_element:
			return EmulationStatus.Unknown
		return mame_statuses.get(driver_element.attrib.get('status'), EmulationStatus.Unknown)

	@property
	def is_skeleton_driver(self):
		#Actually, we're making an educated guess here, as MACHINE_IS_SKELETON doesn't appear directly in the XML...
		#What I actually want to happen is to tell us if a machine will just display a blank screen and nothing else (because nobody wants those in a launcher). Right now that's not really possible without the false positives of games which don't have screens as such but they do display things via layouts (e.g. wackygtr) so the best we can do is say everything that doesn't have any kind of controls.
		return self.number_of_players == 0 and self.overall_status in (EmulationStatus.Broken, EmulationStatus.Unknown)

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
		if not manufacturer:
			self.metadata.publisher = self.metadata.developer = None
			return
		license_match = licensed_arcade_game_regex.fullmatch(manufacturer)
		licensed_from_match = licensed_from_regex.fullmatch(manufacturer)
		hack_match = hack_regex.fullmatch(manufacturer)
		if license_match:
			developer = license_match[1]
			publisher = license_match[2]
		elif licensed_from_match:
			developer = publisher = licensed_from_match[1]
			self.metadata.specific_info['Licensed-From'] = licensed_from_match[2]
		else:
			if not manufacturer.startswith(('bootleg', 'hack')):
				developer = publisher = manufacturer
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

def get_machine(driver):
	return Machine(get_mame_xml(driver))

def mame_verifyroms(basename):
	try:
		#Note to self: Stop wasting time thinking you can make this faster
		subprocess.run(['mame', '-verifyroms', basename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
		return True
	except subprocess.CalledProcessError:
		return False

#Normally we skip over machines that have software lists because it generally indicates they're consoles/computers that should be used with software, these are software lists where the original thing is fine to boot by itself
#Hmm... it's tricky but one might want to blacklist machines that technically can boot by themselves but there's no point doing so (e.g. megacd, gba, other game consoles that don't have inbuilt games), especially once we add software list games into here and it's gonna be a hot mess
#These are prefixes (otherwise I'd have to list every single type of Jakks gamekey thingo)
okay_software_lists = ('vii', 'jakks_gamekey', 'snspell', 'tntell')

def is_actually_machine(machine):
	if machine.xml.attrib.get('runnable', 'yes') == 'no':
		return False

	if machine.xml.attrib.get('isbios', 'no') == 'yes':
		return False

	if machine.xml.attrib.get('isdevice', 'no') == 'yes':
		return False

	return True

def is_machine_launchable(machine):
	needs_software = False
	software_lists = machine.xml.findall('softwarelist')
	for software_list in software_lists:
		software_list_name = software_list.attrib.get('name')
		if software_list_name.startswith(okay_software_lists):
			continue
		needs_software = True
		#print(machine.basename, machine.name, software_list_name)

	if needs_software:
		return False

	if has_mandatory_slots(machine):
		if debug:
			print('%s (%s, %s) has mandatory slots' % (machine.name, machine.basename, machine.source_file))
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
	if machine.is_skeleton_driver:
		#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
		#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up

		#We'll do this check _after_ mame_verifyroms so we don't spam debug print for a bunch of skeleton drivers we don't have
		if debug:
			print('Skipping %s (%s, %s) as it is probably a skeleton driver' % (machine.name, machine.basename, machine.source_file))
		return

	add_metadata(machine)
	if main_config.exclude_non_arcade and machine.metadata.platform == 'Non-Arcade':
		return
	if main_config.exclude_pinball and machine.metadata.platform == 'Pinball':
		return

	machine.make_launcher()

def no_longer_exists(game_id):
	#This is used to determine what launchers to delete if not doing a full rescan
	return not mame_verifyroms(game_id)

def process_machine_element(machine_element):
	machine = Machine(machine_element)
	if machine.source_file in main_config.skipped_source_files:
		return

	if not is_actually_machine(machine):
		return

	if not is_machine_launchable(machine):
		return

	if not mame_verifyroms(machine.basename):
		return

	process_machine(machine)

def process_arcade():
	time_started = time.perf_counter()

	for machine_name, machine_element in iter_mame_entire_xml():
		if not main_config.full_rescan:
			if launchers.has_been_done('MAME machine', machine_name):
				continue

		process_machine_element(machine_element)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Arcade finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

def main():
	if '--drivers' in sys.argv:
		arg_index = sys.argv.index('--drivers')
		if len(sys.argv) == 2:
			print('--drivers requires an argument')
			return

		driver_list = sys.argv[arg_index + 1].split(',')
		for driver_name in driver_list:
			process_machine_element(get_mame_xml(driver_name))
		return

	process_arcade()

if __name__ == '__main__':
	main()
