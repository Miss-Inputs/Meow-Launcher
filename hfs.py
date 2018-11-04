import subprocess
import re

directory_regex = re.compile(r'^d(?: +i)? +(?:(?P<num_items>\d+) items|1 item) +(?P<date>\w{3} [\d ]{2} (?: \d{4}|\d{2}:\d{2})) (?P<name>.+)$')
file_regex = re.compile(r'^(?:f|F) +(?P<type>.{4})/(?P<creator>.{4}) +(?P<resource_size>\d+) +(?P<data_size>\d+) (?P<date>\w{3} [\d ]{2} (?: \d{4}|\d{2}:\d{2})) (?P<name>.+)$')
def parse_list_item(line, path):
	if line.startswith('d'):
		match = directory_regex.match(line)
		if match is None:
			raise Exception(line)

		name = match.group('name')
		return {
			'type': 'folder',
			'path': path + name,
			'name': name,
			'num_items': int(match.group('num_items')) if match.group('num_items') else 1,
			'date': match.group('date')
		}
	elif line.lower().startswith('f'):
		match = file_regex.match(line)
		if match is None:
			raise Exception(line)

		name = match.group('name')
		return {
			'type': 'file',
			'path': path + name,
			'name': name,
			'data_size': int(match.group('data_size')),
			'resource_size': int(match.group('resource_size')),
			'file_type': match.group('type'),
			'creator': match.group('creator'),
			'date': match.group('date')
		}

	raise Exception(line)

file_not_found_regex = re.compile(r'^hls: ".+": no such file or directory$')
def list_inside_hfv(hfv_path, unescaped_name):
	ls_proc = subprocess.run(['hls', '-l', hfv_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='mac-roman', universal_newlines=True)
	if ls_proc.returncode != 0:
		raise Exception('oh no %d' % ls_proc.returncode)

	if file_not_found_regex.fullmatch(ls_proc.stderr.strip()):
		raise FileNotFoundError(hfv_path)

	for line in ls_proc.stdout.split('\n'):
		if line:
			yield parse_list_item(line, unescaped_name if unescaped_name else hfv_path)

def list_recursively(hfv_path, unescaped_name=None):
	for f in list_inside_hfv(hfv_path, unescaped_name):
		if f['type'] == 'folder':
			name = f['name']
			#FIXME: This isn't good, it's quite literally just using wildcards for when there would otherwise be extended characters that hls doesn't recognize. But I guess I can't really do much about that. It sucks at using wildcards too.
			#Damn I wish there was a more modern HFS thing I could use here.
			escaped_name = ''.join([x if ord(x) < 128 else '?' for x in name])
			for ff in list_recursively(hfv_path + escaped_name + ':', f['path'] + ':'):
				yield ff
		else:
			yield f

def list_hfv(hfv_path):
	mount_proc = subprocess.run(['hmount', hfv_path], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
	if mount_proc.returncode != 0:
		raise Exception(mount_proc.stderr)

	try:
		pwd_proc = subprocess.run('hpwd', stdout=subprocess.PIPE, encoding='mac-roman')
		pwd = pwd_proc.stdout.rstrip('\n')

		for f in list_recursively(pwd):

			yield f
	finally:
		umount_proc = subprocess.run('humount')
		if umount_proc.returncode != 0:
			print('Oh no')

def does_exist(hfv_path, inner_path):
	mount_proc = subprocess.run(['hmount', hfv_path], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
	if mount_proc.returncode != 0:
		raise Exception(mount_proc.stderr)

	try:
		list_inside_hfv(inner_path, inner_path)
		return True
	except FileNotFoundError:
		return False
	finally:
		umount_proc = subprocess.run('humount')
		if umount_proc.returncode != 0:
			print('Oh no')

