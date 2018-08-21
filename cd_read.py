import math
import re

from common import read_file

#<type> is BINARY for little endian, MOTOROLA for big endian, or AIFF/WAV/MP3. Generally only BINARY will be used (even audio tracks are usually ripped as raw binary)
cue_file_line_regex = re.compile(r'^\s*FILE\s+(?:"(?P<name>.+)"|(?P<name_unquoted>\S+))\s+(?P<type>.+)\s*$', flags=re.RegexFlag.IGNORECASE)
#<mode> is defined here: https://www.gnu.org/software/ccd2cue/manual/html_node/MODE-_0028Compact-Disc-fields_0029.html#MODE-_0028Compact-Disc-fields_0029 but generally only AUDIO, MODE1/<size>, and MODE2/<size> are used
cue_track_line_regex = re.compile(r'^\s*TRACK\s+(?P<number>\d+)\s+(?P<mode>.+)\s*$', flags=re.RegexFlag.IGNORECASE)

def parse_cue_sheet(cue_path):
	#TODO compressed cue sheet I guess, but who does that?
	files = []

	data = read_file(cue_path).decode('utf8', errors='backslashreplace')
	
	current_file = None
	current_mode = None

	for line in data.splitlines():
		
		file_match = cue_file_line_regex.match(line)
		if file_match:
			if current_file and current_mode:
				files.append((current_file, sector_size_from_cue_mode(current_mode)))
				current_file = None
				current_mode = None

			current_file = file_match['name'] if file_match['name'] else file_match['name_unquoted']
		else:
			#Hhhhhhhhh what am I even doing here? This is like... assuming 1 mode for each file? That can't be right
			if not current_mode:
				track_match = cue_track_line_regex.match(line)
				if track_match:
					current_mode = track_match['mode']
		
	files.append((current_file, sector_size_from_cue_mode(current_mode)))

	return files

def sector_size_from_cue_mode(mode):
	try:
		return int(mode.split('/')[-1])
	except ValueError:
		return 0

def read_mode_1_cd(path, sector_size, seek_to=0, amount=1):
	if sector_size == 2048:
		return read_file(path, seek_to=seek_to, amount=amount)
	elif sector_size == ((12 + 3 + 1) + (4 + 8 + 276) + 2048):
		return sectored_read(path, 12 + 3 + 1, 4 + 8 + 276, 2048, seek_to=seek_to, amount=amount)
	else:
		raise NotImplementedError('no')

def sectored_read(path, raw_header_size, raw_footer_size, data_size, seek_to=0, amount=-1):
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
	sector_count = cooked_position // cooked_sector_size
	total_header_size = raw_header_size * (sector_count + 1)
	total_footer_size = raw_footer_size * sector_count
	return cooked_position + total_header_size + total_footer_size
