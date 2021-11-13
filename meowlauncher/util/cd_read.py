import math
import os
import re
import struct
from typing import Optional
import zlib
from collections.abc import Sequence

from .io_utils import read_file

#<type> is BINARY for little endian, MOTOROLA for big endian, or AIFF/WAV/MP3. Generally only BINARY will be used (even audio tracks are usually ripped as raw binary)
cue_file_line_regex = re.compile(r'^\s*FILE\s+(?:"(?P<name>.+)"|(?P<name_unquoted>\S+))\s+(?P<type>.+)\s*$', flags=re.RegexFlag.IGNORECASE)
#<mode> is defined here: https://www.gnu.org/software/ccd2cue/manual/html_node/MODE-_0028Compact-Disc-fields_0029.html#MODE-_0028Compact-Disc-fields_0029 but generally only AUDIO, MODE1/<size>, and MODE2/<size> are used
cue_track_line_regex = re.compile(r'^\s*TRACK\s+(?P<number>\d+)\s+(?P<mode>.+)\s*$', flags=re.RegexFlag.IGNORECASE)

def parse_cue_sheet(cue_path: str) -> list[tuple[str, int]]:
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
		elif not current_mode:
			#Hhhhhhhhh what am I even doing here? This is like... assuming 1 mode for each file? That can't be right
			track_match = cue_track_line_regex.match(line)
			if track_match:
				current_mode = track_match['mode']

	if current_file and current_mode:
		files.append((current_file, sector_size_from_cue_mode(current_mode)))

	return files

def sector_size_from_cue_mode(mode: str) -> int:
	try:
		return int(mode.split('/')[-1])
	except ValueError:
		return 0

def get_first_data_cue_track(cue_path: str) -> Optional[tuple[str, int]]:
	cue_files = [(f, sector_size) for f, sector_size in parse_cue_sheet(cue_path) if sector_size]
	if not cue_files:
		#The disc probably won't work, but I'll burn that bridge when it happens
		return None
	first_track, sector_size = cue_files[0]
	if not first_track.startswith('/'):
		first_track = os.path.join(os.path.dirname(cue_path), first_track)

	return first_track, sector_size

def read_mode_1_cd(path: str, sector_size: int, seek_to: int=0, amount: int=1) -> bytes:
	if sector_size == 2048:
		return read_file(path, seek_to=seek_to, amount=amount)
	if sector_size == ((12 + 3 + 1) + (4 + 8 + 276) + 2048):
		return sectored_read(path, 12 + 3 + 1, 4 + 8 + 276, 2048, seek_to=seek_to, amount=amount)
	
	raise NotImplementedError('no')

def sectored_read(path: str, raw_header_size: int, raw_footer_size: int, data_size: int, seek_to: int=0, amount: int=-1) -> bytes:
	#Raw header size + raw footer size + data size = total sector size; e.g. 16 + data correction stuff + 2048 = 2532
	#I stole this algorithm from myself, and I forgot how it works
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

def cooked_position_to_real(cooked_position: int, raw_header_size: int, raw_footer_size: int, cooked_sector_size: int) -> int:
	sector_count = cooked_position // cooked_sector_size
	total_header_size = raw_header_size * (sector_count + 1)
	total_footer_size = raw_footer_size * sector_count
	return cooked_position + total_header_size + total_footer_size

def read_gcz(path: str, seek_to=0, amount=-1) -> bytes:
	gcz_header = read_file(path, amount=32)
	#Magic: B10BB10B
	#Sub-type: 4-8 (indicates GC or whatever else)
	compressed_size = int.from_bytes(gcz_header[8:16], 'little')
	#Data size: 16-24 (should be 1.4GB for GameCube)
	if amount == -1:
		amount = int.from_bytes(gcz_header[16:24], 'little')

	block_size = int.from_bytes(gcz_header[24:28], 'little')
	num_blocks = int.from_bytes(gcz_header[28:32], 'little')
	#Block pointers: 8 bytes * [num_blocks]
	#Hashes: 4 bytes * [num blocks] (Adler32)

	#High bit indicates if compressed
	block_pointers = struct.unpack('<%dQ' % num_blocks, read_file(path, seek_to=32, amount=8 * num_blocks))
	hashes = struct.unpack('<%dI' % num_blocks, read_file(path, seek_to=32 + (8 * num_blocks), amount=4 * num_blocks))

	first_block = seek_to // block_size
	end = (seek_to + amount) - 1
	end_block = end // block_size
	blocks_to_read = (end_block - first_block) + 1
	remaining = amount

	data = b''

	position = seek_to
	for i in range(first_block, first_block + blocks_to_read):
		position_in_block = position - (i * block_size)
		bytes_to_read = min(block_size - position_in_block, remaining)

		block = get_gcz_block(path, compressed_size, block_pointers, i, hashes)
		data += block[position_in_block:position_in_block + bytes_to_read]

		position += bytes_to_read
		remaining -= bytes_to_read

	return data

def get_compressed_gcz_block_size(compressed_size: int, block_pointers: Sequence[int], block_num: int) -> int:
	start = block_pointers[block_num]
	if start & (1 << 63):
		start &= ~(1 << 63)
	if block_num < (len(block_pointers) - 1):
		end = block_pointers[block_num + 1]
		if end & (1 << 63):
			end &= ~(1 << 63)
		return end - start

	return compressed_size - start

def get_gcz_block(gcz_path: str, compressed_size: int, block_pointers: Sequence[int], block_num: int, hashes: Sequence[int]) -> bytes:
	#Right after the pointers and then the hashes
	data_offset = 32 + (8 * len(block_pointers)) + (4 * len(block_pointers))

	compressed = True
	compressed_block_size = get_compressed_gcz_block_size(compressed_size, block_pointers, block_num)
	offset = data_offset + block_pointers[block_num]

	if offset & (1 << 63):
		compressed = False
		offset &= ~(1 << 63)

	buf = read_file(gcz_path, seek_to=offset, amount=compressed_block_size)

	expected_hash = hashes[block_num]
	actual_hash = zlib.adler32(buf)
	if expected_hash != actual_hash:
		print(gcz_path, 'block num', block_num, 'might be corrupted! expected =', expected_hash, 'actual =', actual_hash, 'offset =', offset, 'cbs =', compressed_block_size)

	if compressed:
		buf = zlib.decompress(buf)

	return buf
