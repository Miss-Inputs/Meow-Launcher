import os

import archives

def get_real_size(path, compressed_entry=None):
	if compressed_entry is None:
		return os.path.getsize(path)

	return archives.compressed_getsize(path, compressed_entry)

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
