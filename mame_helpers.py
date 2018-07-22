import os
import subprocess
import xml.etree.ElementTree as ElementTree
import re

from metadata import Metadata, EmulationStatus, CPUInfo, ScreenInfo

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
		cpu_info = CPUInfo()
		cpu_info.load_from_xml(main_cpu)

		_lookup_system_cpu_cache[driver_name] = cpu_info
		return cpu_info

	return None

_lookup_system_display_cache = {}
def lookup_system_displays(driver_name):
	if driver_name in _lookup_system_display_cache:
		return _lookup_system_display_cache[driver_name]

	xml = get_mame_xml(driver_name)
	if not xml:
		_lookup_system_display_cache[driver_name] = []
		return None
	machine = xml.find('machine')
	if not machine:
		_lookup_system_display_cache[driver_name] = []
		return None

	displays = machine.findall('display')
	screen_info = ScreenInfo()
	screen_info.load_from_xml_list(displays)
	_lookup_system_display_cache[driver_name] = screen_info
	return screen_info

def get_mame_xml(driver):
	process = subprocess.run(['mame', '-listxml', driver], stdout=subprocess.PIPE)
	status = process.returncode
	output = process.stdout
	if status != 0:
		print('Fucking hell ' + driver)
		return None

	return ElementTree.fromstring(output)

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