"""Manages an unturned server."""
import os
import argparse
import inotify.adapters
from threading import Thread
import subprocess
import re
import time

map_line = re.compile(r'map\s+(\S+)')


threads = []
def on_event(directory, func, types=()):
	thread = Thread(target=_on_event, args=(directory, func, types))
	thread.start()
	threads.append(thread)


def start_server(server_binary, server_name):
	thread = Thread(target=_start_server, args=(server_binary, server_name))
	thread.start()
	threads.append(thread)


def _start_server(server_binary, server_name):
	a = subprocess.Popen([server_binary, '-nographics', '-batchmode', '-easy', '+secureserver/'+server_name])


def wait_for_all():
	for thread in threads:
		thread.join()


def subdirs(path):
	return next(os.walk(path))[1]


def get_world_name(server_data_dir):
	with open(os.path.join(server_data_dir, 'Server', 'Commands.dat'), 'rU') as f:
		for line in f:
			m = map_line.match(line)
			if (m):
				return m.group(1)
	return 'PEI'


def _on_event(directory, func, types):
	print("listening for changes in %s" % directory)
	i = inotify.adapters.Inotify()
	i.add_watch(directory)
	try:
		for event in i.event_gen():
			if event is not None:
				if not types:
					func(event[2], event[3])
				else:
					if all(t in event[1] for t in types):
						func(event[2], event[3])
	except LifetimeFinishedException as e:
		e()
	finally:
		i.remove_watch(directory)


def wait_for_new_player_dir_created(player_data_dir):
	on_event(player_data_dir, on_new_player_first_join, types=('IN_CREATE', 'IN_ISDIR'))


def on_new_player_first_join(watch_path, player_id):
	time.sleep(5)
	player_dir = os.path.join(watch_path, player_id)
	for datfile in ['Clothing.dat', 'Inventory.dat', 'Skills.dat']:
			dst = os.path.join(player_dir, datfile)
			src = os.path.join(player_dir, subdirs(player_dir)[0], 'Player', datfile)
			os.symlink(src, dst)


def configure_existing_players(server_data_dir, player_data_dir):
	map_name = get_world_name(server_data_dir)
	print(map_name)
	for player_id in subdirs(player_data_dir):
		print(player_id)
		map_dir = os.path.join(player_data_dir, player_id, map_name, 'Player')
		if not os.path.exists(map_dir):
			os.makedirs(map_dir)
			for datfile in ['Clothing.dat', 'Inventory.dat', 'Skills.dat']:
				dst = os.path.join(map_dir, datfile)
				src = os.path.join('..', '..', datfile)
				os.symlink(src, dst)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('server_path',
		help='The path to your unturned installation (probably <somewhere>/steamapps/common/Unturned)',
		default='/media/video/steamapps/common/Unturned')
	parser.add_argument('server_name',
		help='The server name (found in .../Unturned/Servers/<THIS>)',
		default='MashedTomatos')
	args = parser.parse_args()
	server_binary = os.path.join(args.server_path, 'Unturned.x86_64')
	server_data_dir = os.path.join(args.server_path, 'Servers', args.server_name)
	player_data_dir = os.path.join(server_data_dir, 'Players')
	start_server(server_binary, args.server_name)
	configure_existing_players(server_data_dir, player_data_dir)
	wait_for_new_player_dir_created(player_data_dir)
	wait_for_all()


if __name__ == '__main__':
	main()