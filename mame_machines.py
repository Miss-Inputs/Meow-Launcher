import subprocess
import xml.etree.ElementTree as ElementTree
import configparser
import os
import sys

import config
import common
import launchers
import emulator_info

debug = '--debug' in sys.argv

def find_main_cpu(machine):
	for chip in machine.findall('chip'):
		tag = chip.attrib['tag']
		if tag == 'maincpu' or tag == 'mainpcb:maincpu':
			return chip

	#If no maincpu, just grab the first CPU chip
	for chip in machine.findall('chip'):
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
	parser.read(config.CATLIST_PATH)
	return parser
	
def get_languages():
	parser = configparser.ConfigParser(interpolation=None, allow_no_value=True)
	parser.optionxform = str
	parser.read(config.LANGUAGES_PATH)
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
		category, _, genres = cat.partition(': ', 1)
		genre, _, subgenre = genres.partition(' / ', 1)
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
	
def process_machine(machine):
	if machine.attrib['runnable'] == 'no':
		return
	if machine.attrib['isbios'] == 'yes':
		return
	if machine.attrib['isdevice'] == 'yes':
		return

	basename = machine.attrib['name']
	family = machine.attrib['cloneof'] if 'cloneof' in machine.attrib else basename
	name = machine.findtext('description')
	
	category, genre, subgenre, is_nsfw = get_category(basename)
	language = get_language(basename)

	if not (machine.find('softwarelist') is None) and family not in config.okay_to_have_software:
		return

	source_file = os.path.splitext(machine.attrib['sourcefile'])[0]
	
	maincpu = find_main_cpu(machine)

	input_element = machine.find('input')
	if input_element is None:
		#Seems like this doesn't actually happen
		input_type = 'No input somehow'
		if debug:
			print('Oi m8', basename, '/', name, 'has no input')
	else:
		control_element = input_element.find('control')
		if control_element is None:
			if 'players' not in input_element.attrib or input_element.attrib['players'] == '0':
				#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
				#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up
				if debug:
					print('Skipping %s (%s) as it has no controls' % (basename, name))
				return
			else:
				input_type = 'Custom'
				#Sometimes you get some games with 1 or more players, but no control type defined.  This usually happens with
				#pinball games and weird stuff like a clock, but also some genuine games like Crazy Fight that are more or less
				#playable just fine, so we'll leave them in
		else:
			input_type = control_element.attrib['type']
			if input_type:
				if input_type == 'doublejoy':
					input_type = 'Twin Joystick'
				elif input_type == 'joy':
					input_type = 'Normal'
				else:
					input_type = input_type.replace('_', ' ').capitalize()
		
	platform = 'Arcade'
	if source_file == 'megatech':
		platform = 'Mega-Tech'
	elif source_file == 'megaplay':
		platform = 'Mega-Play'
	elif source_file == 'playch10':
		platform = 'PlayChoice-10'
	elif source_file == 'nss':
		platform = 'Nintendo Super System'
	elif category == 'Game Console':
		platform = 'Plug & Play' 
		#Since we're skipping over stuff with software lists, anything that's still classified as a game console is a plug &
        #play system
	elif category == 'Handheld':
		platform = 'Handheld' 
		#Could also be a tabletop system which takes AC input, but since catlist.ini doesn't take that into account, I don't
		#really have a way of doing so either
	elif category == 'Misc.':
		platform = genre
	elif category == 'Computer':
		platform = 'Computer'
	elif genre == 'Electromechanical' and subgenre == 'Reels':
		platform = 'Pokies'
		category = 'Pokies'
	elif genre == 'Electromechanical' and subgenre == 'Pinball':
		platform = 'Pinball'
		category = 'Pinball'
		
	if language is not None and language != 'English':
		category += ' untranslated'
	
	metadata = {
		'Main-CPU': None if maincpu is None else maincpu.attrib['name'], 
		'Main-Input': input_type, 
		'Emulation-Status': machine.find('driver').attrib['status'], 
		'Source-File': source_file, 
		'Genre': genre, 
		'Subgenre': subgenre, 
		'NSFW': is_nsfw, 
		'Languages': language, 
		'Family': family,
		'Year': machine.findtext('year'),
		'Author': machine.findtext('manufacturer'),
		#Some other things we could get from XML if we decide we care about it:
		#Display type/resolution/refresh rate/number of screens
		#Sound channels
		#Number of players
	}

	command_line = emulator_info.make_mame_command_line(basename)
	launchers.make_launcher(platform, command_line, name, [category, genre, source_file], metadata)
		
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
		process_machine(xml.find('machine'))
