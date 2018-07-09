import re
import os
import shlex

import config
import common

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
def base_make_desktop(command, display_name, comment, platform, categories=[], tags=[], metadata={}, ext=''):
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

		if categories:
			f.write('X-Categories=%s\n' % (';'.join(categories)))

		if tags:
			f.write('X-Filename-Tags=%s\n' % (';'.join(tags)))

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

def make_desktop(platform, command, path, name, categories=[], metadata={}, ext='', compressed_entry=None):
	#Use compressed_entry for manual decompression, don't do it if the compression format is natively supported by the emulator
	if compressed_entry:
		extracted_path = os.path.join('/tmp/crappyromlauncher', compressed_entry)
		inner_cmd = command.format(shlex.quote(extracted_path))
		cmd = 'sh -c {0}'.format(shlex.quote('7z x -o/tmp/crappyromlauncher {0}; {1}; rm -rf /tmp/crappyromlauncher'.format(shlex.quote(path), inner_cmd)))	
	else:
		cmd = command.format(shlex.quote(path))

	display_name = make_display_name(name)
	comment = name
	filename_tags = common.find_filename_tags.findall(name)
	base_make_desktop(cmd, display_name, comment, platform, categories, filename_tags, metadata, ext)
