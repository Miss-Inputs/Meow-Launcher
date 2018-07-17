#!/usr/bin/env python3

import subprocess
import xml.etree.ElementTree as ElementTree
import configparser
import os
import sys

import config
import common
import launchers
import emulator_info
from metadata import Metadata, EmulationStatus

debug = '--debug' in sys.argv


_lookup_system_cpu_cache = {}
def lookup_system_cpu(driver_name):
	if driver_name in _lookup_system_cpu_cache:
		return _lookup_system_cpu_cache[driver_name]

	xml = get_mame_xml(driver_name)
	if not xml:
		_lookup_system_cpu_cache[driver_name] = None
		return None
	machine = xml.find('machine')
	if not machine:
		_lookup_system_cpu_cache[driver_name] = None
		return None

	main_cpu = find_main_cpu(machine)
	if main_cpu is not None: #"if main_cpu: doesn't work. Frig! Why not! Wanker! Sodding bollocks!
		_lookup_system_cpu_cache[driver_name] = main_cpu
		return main_cpu

	return None

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
		command_line = emulator_info.make_mame_command_line(self.basename)
		launchers.make_launcher(command_line, self.name, self.metadata)


def find_main_cpu(machine_xml):
	for chip in machine_xml.findall('chip'):
		tag = chip.attrib['tag']
		if tag == 'maincpu' or tag == 'mainpcb:maincpu':
			return chip

	#If no maincpu, just grab the first CPU chip
	for chip in machine_xml.findall('chip'):
		if chip.attrib['type'] == 'cpu':
			return chip

	#Alto I and HP 2100 have no chips, apparently.  Huh?  Oh well
	return None

def mame_verifyroms(basename):
	#FIXME Okay this is way too fuckin' slow
	status = subprocess.run(['mame', '-verifyroms', basename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
	return status == 0

def get_catlist():
	parser = configparser.ConfigParser(interpolation=None, allow_no_value=True)
	parser.optionxform = str
	parser.read(config.catlist_path)
	return parser
	
def get_languages():
	parser = configparser.ConfigParser(interpolation=None, allow_no_value=True)
	parser.optionxform = str
	parser.read(config.languages_path)
	return parser

catlist = get_catlist()
languages = get_languages()

def get_category(basename):
	cat = None
	for section in catlist.sections():
		if basename in catlist[section]:
			cat = section
			break
	if not cat:
		return 'Unknown', 'Unknown', 'Unknown', 'Unknown'

	if ': ' in cat:
		category, _, genres = cat.partition(': ')
		genre, _, subgenre = genres.partition(' / ')
		is_nsfw = False
		if subgenre.endswith('* Mature *'):
			is_nsfw = True
			subgenre = subgenre[:-10]
		
		return category, genre, subgenre, is_nsfw
	
	category, genre = cat.split(' / ', 1)
	return category, genre, None, False
		
def get_language(basename):
	lang = None
	for section in languages.sections():
		if basename in languages[section]:
			lang = section
			break
			
	return lang

def get_input_type(machine):
	input_element = machine.xml.find('input')
	if input_element is None:
		#Seems like this doesn't actually happen
		if debug:
			print('Oi m8', machine.basename, '/', machine.name, 'has no input')
		return 'No input somehow'

	control_element = input_element.find('control')
	if control_element is None:
		if 'players' not in input_element.attrib or input_element.attrib['players'] == '0':				
			return None
			
		return 'Custom'
		#Sometimes you get some games with 1 or more players, but no control type defined.  This usually happens with
		#pinball games and weird stuff like a clock, but also some genuine games like Crazy Fight that are more or less
		#playable just fine, so we'll leave them in

	input_type = control_element.attrib['type']
	if input_type:
		if input_type == 'doublejoy':
			return 'Twin Joystick'
		elif input_type == 'joy':
			return 'Normal'
		elif input_type == 'lightgun':
			return 'Light Gun'
				
		return input_type.replace('_', ' ').capitalize()

	if debug:
		print("This shouldn't happen either but for", machine.basename, "it did")
	return None

def add_machine_platform(machine):
	machine.metadata.platform = 'Arcade'
	category = machine.metadata.categories[0]

	if machine.source_file == 'megatech':
		machine.metadata.platform = 'Mega-Tech'
	elif machine.source_file == 'megaplay':
		machine.metadata.platform = 'Mega-Play'
	elif machine.source_file == 'playch10':
		machine.metadata.platform = 'PlayChoice-10'
	elif machine.source_file == 'nss':
		machine.metadata.platform = 'Nintendo Super System'
	elif category == 'Game Console':
		machine.metadata.platform = 'Plug & Play' 
		#Since we're skipping over stuff with software lists, anything that's still classified as a game console is a plug &
        #play system
	elif category == 'Handheld':
		machine.metadata.platform = 'Handheld' 
		#Could also be a tabletop system which takes AC input, but since catlist.ini doesn't take that into account, I don't
		#really have a way of doing so either
		if machine.name.startswith('Game & Watch: '):
			#Source file is hh_sm510 so we can't detect the Game & Watchiness of a handheld game from that
			machine.metadata.platform, _, machine.name = machine.name.partition(': ')
	elif category == 'Misc.':
		machine.metadata.platform = machine.metadata.genre
	elif category == 'Computer':
		machine.metadata.platform = 'Computer'
	elif machine.metadata.genre == 'Electromechanical' and machine.metadata.subgenre == 'Reels':
		machine.metadata.platform = 'Pokies'
	elif machine.metadata.genre == 'Electromechanical' and machine.metadata.subgenre == 'Pinball':
		machine.metadata.platform = 'Pinball'

def format_clock_speed(hertz, precision=3):
	if hertz >= 1_000_000_000:
		return ('{0:.' + str(precision) + 'g} GHz').format(hertz / 1_000_000_000)
	elif hertz >= 1_000_000:
		return ('{0:.' + str(precision) + 'g} MHz').format(hertz / 1_000_000)
	elif hertz >= 1_000:
		return ('{0:.' + str(precision) + 'g} KHz').format(hertz / 1_000)
	else:
		return ('{0:.' + str(precision) + 'g} Hz').format(hertz)

def find_aspect_ratio(width, height):
	for i in reversed(range(1, max(int(width), int(height)) + 1)):
		if (width % i) == 0 and (height % i) == 0:
			return '{0:.0f}:{1:.0f}'.format(width // i, height // i)

	#This wouldn't happen unless one of the arguments is 0 or something silly like that
	return None
	
def add_metadata(machine):
	category, genre, subgenre, nsfw = get_category(machine.basename)
	machine.metadata.categories = [category] if category else ['Unknown']
	machine.metadata.genre = genre
	machine.metadata.subgenre = subgenre
	machine.metadata.nsfw = nsfw

	main_cpu = find_main_cpu(machine.xml)
	if main_cpu is not None: #Why?
		machine.metadata.main_cpu = main_cpu.attrib['name']
		if main_cpu.attrib['name'] != 'Netlist CPU Device' and 'clock' in main_cpu.attrib:
			try:
				machine.metadata.clock_speed = format_clock_speed(int(main_cpu.attrib['clock']))
			except ValueError:
				pass

	resolutions = []
	refresh_rates = []
	aspect_ratia = []
	for display in machine.xml.findall('display'):
		machine.metadata.number_of_screens += 1
		display_type = display.attrib['type']
		if display_type == 'raster' or display_type == 'lcd':
			width = display.attrib['width']
			height = display.attrib['height']
			resolutions.append('{0}x{1}'.format(width, height))
			try:
				aspect_ratia.append(find_aspect_ratio(float(width), float(height)))
			except ValueError:
				pass
		else:
			#Vector or SVG-based LCD
			resolutions.append(display_type.capitalize())	
		
		if 'refresh' in display.attrib:
			try:
				refresh_rates.append(format_clock_speed(float(display.attrib['refresh']), 4))
			except ValueError:
				#Hasn't happened so far, but just in case
				refresh_rates.append(display.attrib['refresh'])
	machine.metadata.screen_resolution = ' + '.join(resolutions)
	machine.metadata.refresh_rate = ' + '.join(refresh_rates)
	machine.metadata.aspect_ratio = ' + '.join(aspect_ratia)
		
	add_machine_platform(machine)

	language = get_language(machine.basename)
	if language:
		machine.metadata.languages = [language]
	
	machine.metadata.emulator_name = 'MAME'
	machine.metadata.year = machine.xml.findtext('year')
	machine.metadata.author = machine.xml.findtext('manufacturer')
	
	emulation_status = machine.xml.find('driver').attrib['status']
	if emulation_status == 'good':
		machine.metadata.emulation_status = EmulationStatus.Good
	elif emulation_status == 'imperfect':
		machine.metadata.emulation_status = EmulationStatus.Imperfect
	elif emulation_status == 'preliminary':
		machine.metadata.emulation_status = EmulationStatus.Broken	
	
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

	input_type = get_input_type(machine)
	if not input_type:
		#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
		#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up
		if debug:
			print('Skipping %s (%s) as it has no controls' % (machine.basename, machine.name))
		return
	machine.metadata.input_method = input_type
	machine.metadata.specific_info['Family'] = machine.family

	add_metadata(machine)
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
	
def get_mame_xml(driver):
	process = subprocess.run(['mame', '-listxml', driver], stdout=subprocess.PIPE)
	status = process.returncode
	output = process.stdout
	if status != 0:
		print('Fucking hell ' + driver)
		return None

	return ElementTree.fromstring(output)

def process_arcade():
	#Fuck iterparse by the way, if you stumble across this script and think "oh you should use iterparse instead of this
	#kludge!" you are wrong
	#(Okay, if you want an attempt at a reason why: I've tried it, and MAME's machine elements are actually more
	#complicated and seemingly refer to other machine elements that are displayed alongside the main one with an
	#individual -listxml)
	#Could it be faster to use -verifyroms globally and parse the output somehow and then get individual XML from
	#successful results?

	for driver, source_file in get_mame_drivers():
		if source_file in config.too_slow_drivers:
			continue
			
		if common.starts_with_any(source_file, config.skip_fruit_machines):
			#Get those fruit machines outta here (they take too long to process and verify that we don't have them, and tend to
			#not work anyway, otherwise I'd consider still including them)
			continue

		#You probably think this is why it's slow, right?  You think "Oh, that's silly, you're verifying every single romset
		#in existence before just getting the XML", that's what you're thinking, right?  Well, I am doing that, but as it
		#turns out if I do the verification inside process_machine it takes a whole lot longer.  I don't fully understand why
		#but I'll have you know I actually profiled it
		if not mame_verifyroms(driver):
			continue

		xml = get_mame_xml(driver)
		if xml is None:
			continue
		process_machine(Machine(xml.find('machine')))

if __name__ == '__main__':
	os.makedirs(config.output_folder, exist_ok=True)
	process_arcade()
