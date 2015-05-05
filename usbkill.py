#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
 
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Contact: hephaestos@riseup.net - 8764 EF6F D5C1 7838 8D10 E061 CF84 9CE5 42D0 B12B

import re
import subprocess
import os, sys, signal
from time import time, sleep

# We compile this function beforehand for efficiency.
DEVICE_RE = re.compile(".+ID\s(?P<id>\w+:\w+)")

help_message = "usbkill is a simple program with one goal: quickly shutdown the computer when a usb is inserted or removed.\nIt logs to /var/log/usbkill/kills.log\nYou can configure a whitelist of usb ids that are acceptable to insert and the remove.\nThe usb id can be found by running the command 'lsusb'.\nSettings can be changed in /etc/usbkill/settings\n\nIn order to be able to shutdown the computer, this program needs to run as root.\n"

def log(msg):
	logfile = " /var/log/usbkill/usbkill.log"
	
	# Empty line to separate log enties
	os.system("echo '' >> " + logfile)
	
	# Log the message that needed to be logged:
	os.system("echo '" + str(time) + " " + msg + "' >> " + logfile)
	
	# Log current usb state:
	os.system("echo 'Current state:' >> " + logfile)
	os.system("lsusb >> " + logfile)
	
def kill_computer():
	# Log what is happening:
	log("Detected usb change. Dumping lsusb and killing computer...")
	
	# Sync the filesystem so that the recent log entry does not get lost.
	os.system("sync")
	
	# This function will poweroff your computer immediately
	os.system("poweroff -f")

def lsusb():
	# A python version of the command 'lsusb' that returns a list of connected usbids
	df = subprocess.check_output("lsusb", shell=True).decode('utf-8')
	devices = []
	for line in df.split('\n'):
		if line:
		    info = DEVICE_RE.match(line)
		    if info:
		        dinfo = info.groupdict()
		        devices.append(dinfo['id'])
	return devices

def settings_template(filename):
	if not os.path.isfile(filename):
		# Pre-populate the settings file if it does not exist yet
		f = open(filename, 'w')
		f.write("# whitelist command lists the usb ids that you want whitelisted\n")
		f.write("# find the correct usbid for your trusted usb using the command 'lsusb'\n")
		f.write("# usbid looks something line 0123:9abc\n")
		f.write("# Be warned! other parties can copy your trusted usbid to another usb device!\n")
		f.write("# use whitelist command and single space separation as follows:\n")
		f.write("# whitelist usbid1 usbid2 etc\n")
		f.write("whitelist \n\n")
		f.write("# allow for a certain amount of sleep time between checks, e.g. 0.5 seconds:\n")
		f.write("sleep 0.5\n")
		f.close()

def load_settings(filename='/etc/usbkill/settings'):
	# read all lines of settings file
	f = open(filename, 'r')
	lines = f.readlines()
	f.close()
	
	# Find the only two supported settings
	devices = None
	sleep_time = None
	for line in lines:
		if line[:10] == "whitelist ":
			devices = line.replace("\n","").replace("  "," ").split(" ")[1:]
		if line[:6] == "sleep ":
			sleep_time = float(line.replace("\n","").replace("  "," ").split(" ").pop())

	assert not None in [devices, sleep_time], "Please set the 'sleep' and 'whitelist' parameters in '/etc/usbkill/settings' !"
	assert sleep_time > 0.0, "Please allow for positive non-zero 'sleep' delay between usb checks!"
	return devices, sleep_time
	
def loop():
	# Main loop that checks every 'sleep_time' seconds if computer should be killed.
	# Allows only whitelisted usb devices to connect!
	# Allows no usb device that wat present during program start to disconnect!
	start_devices = lsusb()
	whitelisted_devices, sleep_time = load_settings()
	acceptable_devices = set(start_devices + whitelisted_devices)
	
	# Write to logs that loop is starting:
	log("Started patrolling the usb ports every ", sleep_time, " seconds.")
	
	# Main loop
	while True:
		# List the current usb devices
		current_devices = lsusb()
		
		# Check that all current devices are in the set of acceptable devices
		for device in current_devices:
			if device not in acceptable_devices:
				kill_computer()
				
		# Check that all start devices are still present in current devices
		for device in start_devices:
			if device not in current_devices:
				kill_computer()
				
		sleep(sleep_time)

def exit_handler(signum, frame):
	print("\nExiting because exit signal was received\n")
	log("Exiting because exit signal was received")
	sys.exit(0)

if __name__=="__main__":
	# Check arguments
	args = sys.argv[1:]
	if '-h' in args or '--help' in args:
		sys.exit(help_message)
	elif len(args) > 0:
		sys.exit("\nArgument not understood. Can only understand -h\n")
		
	# Check if program is run as root, else exit.
	# Root is needed to power off the computer.
	if not os.geteuid() == 0:
		sys.exit("\nThis program needs to run as root.\n")
	
	# Make sure there is a logging folder
	if not os.path.isdir("/var/log/usbkill/"):
		os.system("mkdir /var/log/usbkill/")
	
	# Make sure settings file is available
	settings_template(filename)
	

	# Register handlers for clean exit of loop
	for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT, ]:
		signal.signal(sig, exit_handler)
		
	# Start main loop
	loop()
	
