import re
import os
import math

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

def read_mode_1_cd(path, sector_size, seek_to=0, amount=1):
	if sector_size == 2048:
		return read_file(path, seek_to=seek_to, amount=amount)
	elif sector_size == ((12 + 3 + 1) + (4 + 8 + 276) + 2048):
		return sectored_read(path, 12 + 3 + 1, 4 + 8 + 276, 2048, seek_to=seek_to, amount=amount)
	else:
		raise NotImplementedError('no')

def sectored_read(path, raw_header_size, raw_footer_size, data_size, seek_to=0, amount=-1):
	#For CD handling
	#Raw header size + raw footer size + data size = total sector size; e.g. 16 + data correction stuff + 2048 = 2532
	#I stole this algorithm from myself, and I forgot how it works
	#It might not work at all for multiple sectors, but uhhh I guess we'll see
	#TODO: Compressed files _I guess_?
	end = seek_to + amount
	start = cooked_position_to_real(seek_to, raw_header_size, raw_footer_size, data_size)
	raw_end = cooked_position_to_real(end, raw_header_size, raw_footer_size, data_size)
	raw_count = (raw_end - start) + 1 

	number_of_sectors = int(math.ceil((raw_count - amount) / ((raw_header_size + raw_footer_size) + 1)))
	
	if number_of_sectors == 1:
		return read_file(path, seek_to=start, amount=amount)
	
	#We're crossing sectors? Crap...
	start_sector = int(math.ceil(seek_to / data_size))
	start_offset_in_sector = int(seek_to % data_size)
	end_sector = int(math.ceil(end / data_size))
	end_offset_in_sector = int(end % data_size)
	
	#Read remainder of the start sector first
	result = read_file(path, seek_to=start, amount=data_size - start_offset_in_sector)
	
	#Read any sectors between start and end
	for i in range(0, number_of_sectors - 2):
		this_sector_start = cooked_position_to_real(data_size * (start_sector + i + 1), raw_header_size, raw_footer_size, data_size)
		result += read_file(path, seek_to=this_sector_start, amount=data_size)
		
	#Read as much out of the end sector as needed
	end_sector_start = cooked_position_to_real(data_size * end_sector, raw_header_size, raw_footer_size, data_size)
	result += read_file(path, seek_to=end_sector_start, amount=end_offset_in_sector + 1)
	return result

def cooked_position_to_real(cooked_position, raw_header_size, raw_footer_size, cooked_sector_size):
	sector_count = int(math.ceil(cooked_position / cooked_sector_size))
	total_header_size = raw_header_size * (sector_count + 1)
	total_footer_size = raw_footer_size * sector_count
	return cooked_position + total_header_size + total_footer_size
	
def read_file(path, compressed_entry=None, seek_to=0, amount=-1):
	if compressed_entry is None:
		with open(path, 'rb') as f:
			f.seek(seek_to)
			if amount < 0:
				return f.read()
			
			return f.read(amount)
	
	
	data = archives.compressed_get(path, compressed_entry)
	if seek_to:
		if amount > -1:
			return data[seek_to: seek_to + amount]
		return data[seek_to:]
	
	if amount > -1:
		return data[:amount]

	return data	

class NotAlphanumericException(Exception):
	pass

def convert_alphanumeric(byte_array):
	string = ''
	for byte in byte_array:
		char = chr(byte)
		if char not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
			raise NotAlphanumericException(char)
		string += char
	return string
