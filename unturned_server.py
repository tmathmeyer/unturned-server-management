"""Manages an unturned server."""
import os
import argparse
import inotify.adapters
from threading import Thread
import subprocess
import re

map_line = re.compile(r'map\s+\S+')


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
	return next(os.walk('.'))[1]

class LifetimeFinishedException(Exception):
	def __init__(self, finished, *args, **kwargs):
		self.cb = finished
		self.args = args
		self.kwargs = kwargs

	def __call__(self,):
		self.cb(*self.args, **self.kwargs)



def get_world_name(server_data_dir):
	with open(os.path.join(server_data_dir, 'Server', 'Commands.dat'), 'rU') as f:
		for line in f:
			m = map_line.match(line)
			if (m):
				return m.group(0)
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

def wait_for_player_join_new_world(player_path, new_player):
	on_event(player_path, on_world_directory_created(new_player), types=('IN_CREATE', 'IN_ISDIR'))

def on_world_directory_created(new_player):
	def __stub__(watch_path, filename):
		player_dir = os.path.join(watch_path, filename, 'Player')
		os.makedirs(player_dir)
		print('created world directory (%s/%s) user_new=%s' % (watch_path, filename, new_player))
		if not new_player:
			for datfile in ['Clothing.dat', 'Inventory.dat', 'Skills.dat']:
				dst = os.path.join(player_dir, datfile)
				src = os.path.join('..', '..', datfile)
				os.symlink(src, dst)
		else:
			for datfile in ['Clothing.dat', 'Inventory.dat', 'Skills.dat']:
				dst = os.path.join(watch_path, datfile)
				src = os.path.join(player_dir, datfile)
				os.symlink(src, dst)
			raise LifetimeFinishedException(wait_for_player_join_new_world, watch_path, False)
	return __stub__

def wait_for_player_first_join(player_data_dir):
	on_event(player_data_dir, on_new_player_first_join, types=('IN_CREATE', 'IN_ISDIR'))

def on_new_player_first_join(watch_path, filename):
	wait_for_player_join_new_world(os.path.join(watch_path, filename), True)



def configure_existing_players(server_data_dir, player_data_dir):
	map_name = get_world_name(serveR_data_dir)
	for player_id in subdirs(player_data_dir):
		map_dir = os.path.join(player_data_dir, player_id, map_name, 'Player')
		if not os.path.exists(map_dir):
			os.makedirs(map_dir)
			for datfile in ['Clothing.dat', 'Inventory.dat', 'Skills.dat']:
				dst = os.path.join(map_dir, datfile)
				src = os.path.join('..', '..', datfile)
				os.symlink(src, dst)




if __name__ == '__main__':
	server_dir = '/media/video/steamapps/common/Unturned'
	server_binary = os.path.join(server_dir, 'Unturned.x86_64')
	server_name = 'MashedTomatos2'
	server_data_dir = os.path.join(server_dir, 'Servers', server_name)
	player_data_dir = os.path.join(server_data_dir, 'Players')

	start_server(server_binary, server_name)

	wait_for_player_first_join(player_data_dir)
	wait_on_all_existing_players(player_data_dir)
	wait_for_all()



