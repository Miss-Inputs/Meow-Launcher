#!/usr/bin/env python3

import configparser
import os
import re
import itertools
import collections
import sys

import config
import launchers

debug = '--debug' in sys.argv
super_debug = '--super-debug' in sys.argv

def update_name(desktop, disambiguator, disambiguation_method):
	if not disambiguator:
		return
	entry = desktop[1]['Desktop Entry']
	if super_debug:
		print('Disambiguating', entry['Name'], 'with', disambiguator, 'using', disambiguation_method)
	if 'X-Ambiguous-Name' not in entry:
		entry['X-Ambiguous-Name'] = entry['Name']
	if 'X-Disambiguator' not in entry:
		entry['X-Disambiguator'] = disambiguator
	else:
		entry['X-Disambiguator'] += ';' + disambiguator
	entry['Name'] += ' ' + disambiguator
		
	writer = configparser.ConfigParser(interpolation=None)
	writer.optionxform = str 
	#You don't fucking understand .desktop files are case sensitive you're fucking
	#them up by fucking up the case for fucks sake stop it who asked you to do
	#that you stupid fuckwit
	writer.read_dict(desktop[1])
	with open(desktop[0], 'wt') as f:
		writer.write(f)

def resolve_duplicates_by_metadata(group, field, format_function=None):
	value_counter = collections.Counter(launchers.get_field(d[1], field) for d in group)
	for dup in group:
		field_value = launchers.get_field(dup[1], field)
		name = launchers.get_field(dup[1], 'Name')
			
		#See if this launcher is unique in this group (of launchers with the same
		#name) for its field.  If it's the only launcher for this field, we can
		#use Thing (Field) as the final display name to avoid ambiguity
		if value_counter[field_value] == 1:
			if field_value != name and field_value is not None:
				#Avoid "Doom (Doom)" and "Blah (None)" and such; in those cases, just leave it as "Doom" or "Blah"
				update_name(dup, format_function(field_value) if format_function else '({0})'.format(field_value), field)
		else:
			if value_counter[field_value] == len(group):
				#Field is the same across the whole group.  Need to disambiguate some
				#other way
				pass
			else:
				#Field is different, but still requires disambiguation.  That is to say,
				#there is something else with the same field in this group, but we still
				#need to append the field to disambiguate it from other stuff
				if field_value != name and field_value is not None:
					update_name(dup, format_function(field_value) if format_function else '({0})'.format(field_value), field)
				
def resolve_duplicates_by_filename_tags(group):
	for dup in group:
		the_rest = [d for d in group if d[0] != dup[0]]
		tags = launchers.get_array(dup[1], 'X-Filename-Tags')
		name = launchers.get_field(dup[1], 'Name')
		
		differentiator_candidates = []
		
		rest_tags = [launchers.get_array(rest[1], 'X-Filename-Tags') for rest in the_rest]
		for tag in tags:
			if not all([tag in rest_tag for rest_tag in rest_tags]):
				differentiator_candidates.append(tag)
		
		if differentiator_candidates:
			update_name(dup, ' '.join(differentiator_candidates), 'tags')

def resolve_duplicates(group, method, format_function=None):
	if method == 'tags':
		resolve_duplicates_by_filename_tags(group)
	else:
		resolve_duplicates_by_metadata(group, method, format_function)

def normalize_name(name):
	name = name.lower()
	name = re.sub(r'\.\B', '', name)
	name = name.replace('3-D', '3D')
	name = name.replace('&', 'and')
	name = name.replace(" 'n", "'n")
	name = re.sub(r'\b-\b', ' ', name)
	name = name.replace(': ', ' - ')
	name = name.replace('é', 'e')
	name = name.replace('!', '')
	name = name.replace('Dr. ', 'Dr ')
	
	return name

def fix_duplicate_names(method, format_function=None):
	files = [(path, launchers.convert_desktop(path)) for path in [os.path.join(config.output_folder, f) for f in os.listdir(config.output_folder)]]

	keyfunc = lambda f: normalize_name(launchers.get_field(f[1], 'Name'))
	files.sort(key=keyfunc)
	duplicates = {}
	for key, group in itertools.groupby(files, key=keyfunc):
		g = list(group)
		if len(g) > 1:
			duplicates[key] = g

	for k, v in duplicates.items():
		if method == 'check':
			print('Duplicate name still remains: ', k, [d[1]['Desktop Entry']['Comment'] for d in v])
		else:
			resolve_duplicates(v, method, format_function)

def revision_disambiguate(rev):
	if rev == '0':
		return None
	
	if rev.isdigit() and len(rev) == 1:
		return '(Rev ' + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[int(rev) - 1] + ')'

	return '(Rev {0})'.format(rev)
	
def disambiguate_names():
	fix_duplicate_names('X-Platform')
	fix_duplicate_names('X-Regions', lambda regions: '({0})'.format(regions.replace(';', ', ')))
	fix_duplicate_names('X-Publisher')
	fix_duplicate_names('X-Developer')
	fix_duplicate_names('X-Revision', revision_disambiguate)
	fix_duplicate_names('X-Year')
	fix_duplicate_names('X-Languages', lambda languages: '({0})'.format(languages.replace(';', ', ')))
	fix_duplicate_names('tags')
	fix_duplicate_names('X-Extension', lambda ext: '(.{0})'.format(ext))
	if debug:
		fix_duplicate_names('check')

if __name__ == '__main__':
	disambiguate_names()
