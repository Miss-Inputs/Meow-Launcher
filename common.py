import re
import os

import archives

find_filename_tags = re.compile(r'(\([^)]+?\)+|\[[^]]+?\]+)')
remove_extra_spaces = re.compile(r'\s(?=\s|$)')
def remove_filename_tags(name):
	if name.startswith(('(', '[')) and name.endswith((')', ']')):
		return name	
	
	return remove_extra_spaces.sub('', find_filename_tags.sub('', name))

def starts_with_any(s, prefixes):
	#Allows s.startswith() with any iterable, not just tuple
	for prefix in prefixes:
		if s.startswith(prefix):
			return True
	return False

def get_real_size(path, compressed_entry=None):
	if compressed_entry is None:
		return os.path.getsize(path)
		
	return archives.compressed_getsize(path, compressed_entry)
	
def read_file(path, compressed_entry=None):
	#TODO: Do a thing where we can just read a small part of the file instead of slurping the whole thing (impossible if
	#it's compressed, though)
	if compressed_entry is None:
		with open(path, 'rb') as f:
			return f.read() 
	else:
		return archives.compressed_get(path, compressed_entry)
