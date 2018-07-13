import re
import os
import shlex
import configparser

import config
import common

def convert_desktop(path):
	parser = configparser.ConfigParser(interpolation=None)
	parser.optionxform = str #Can you actually fuck off?
	parser.read(path)
	return {section: {k: v for k, v in parser.items(section)} for section in parser.sections()}

def get_field(desktop, name):
	entry = desktop['Desktop Entry']
	if name in entry:
		return entry[name]
	
	return None

def get_array(desktop, name):
	field = get_field(desktop, name)
	if field is None:
		return []
	
	return field.split(';')

remove_brackety_things_for_filename = re.compile(r'[]([)]')
clean_for_filename = re.compile(r'[^A-Za-z0-9_]')
def make_filename(name):
	name = name.lower()
	name = remove_brackety_things_for_filename.sub('', name)
	name = clean_for_filename.sub('-', name)
	while name.startswith('-'):
		name = name[1:]
	return name

used_filenames = []
def base_make_desktop(command, display_name, comment, platform, categories=None, tags=None, metadata=None, ext=''):
	base_filename = make_filename(display_name)
	filename = base_filename + '.desktop'
	
	i = 0
	while filename in used_filenames:
		filename = base_filename + str(i) + '.desktop'
		i += 1
	
	path = os.path.join(config.output_folder, filename)
	used_filenames.append(filename)

	with open(path, 'wt') as f:
		f.write('[Desktop Entry]\n')
		f.write('Type=Application\n')
		f.write('Encoding=UTF-8\n')
		f.write('Name=%s\n' % display_name)
		f.write('Comment=%s\n' % comment)
		f.write('Exec=%s\n' % command)
		f.write('X-Platform=%s\n' % platform)

		#TODO: Categories, tags should be part of metadata anyway
		if categories:
			f.write('X-Categories=%s\n' % (';'.join(categories)))

		if tags:
			f.write('X-Filename-Tags=%s\n' % (';'.join(tags)))

		if metadata:
			for k, v in metadata.items():
				if v:
					f.write('X-{0}={1}\n'.format(k.replace('_', '-'), v))
		
		if ext:
			f.write('X-Extension=%s\n' % ext)

		os.chmod(path, 0o7777)

def make_display_name(name):
	display_name = common.remove_filename_tags(name)
		
	for replacement in config.name_replacement:
		display_name = re.sub(r'(?<!\w)' + re.escape(replacement[0]) + r'(?!\w)', replacement[1], display_name, flags=re.I)
	for replacement in config.add_the:
		display_name = re.sub(r'(?<!The )' + re.escape(replacement), 'The ' + replacement, display_name, flags=re.I)
	for replacement in config.subtitle_removal:
		display_name = re.sub(r'^' + re.escape(replacement[0]) + r'(?!\w)', replacement[1], display_name, flags=re.I)
			
	return display_name

def make_desktop(platform, command, path, name, categories=None, metadata=None, ext='', compressed_entry=None):
	#Use compressed_entry for manual decompression, don't pass that if the compression format is natively supported by the
	#emulator
	if compressed_entry:
		temp_folder = '/tmp/temporary_rom_extract'
		#TODO: Should I get the inner shell to ensure this directory exists, or to make a new one entirely?
		extracted_path = os.path.join(temp_folder, compressed_entry)
		inner_cmd = command.format(shlex.quote(extracted_path))
		shell_command = shlex.quote('7z x -o{2} {0}; {1}; rm -rf {2}'.format(shlex.quote(path), inner_cmd, temp_folder))
		cmd = 'sh -c {0}'.format(shell_command)
	else:
		cmd = command.format(shlex.quote(path))

	display_name = make_display_name(name)
	comment = name
	filename_tags = common.find_filename_tags.findall(name)
	base_make_desktop(cmd, display_name, comment, platform, categories, filename_tags, metadata, ext)
