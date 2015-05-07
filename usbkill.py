#!/usr/bin/env python3
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
import platform
import os, sys, signal
import configparser
from time import time, sleep
from datetime import datetime

# We compile this function beforehand for efficiency.
DEVICE_RE = re.compile(".+ID\s(?P<id>\w+:\w+)")

# Set the global settings path
SETTINGS_FILE = '/etc/usbkill/settings.ini'

# Get the current platform
CURRENT_PLATFORM = platform.system().upper()

help_message = """usbkill is a simple program with one goal: quickly shutdown the computer when a usb is inserted or removed.
It logs to /var/log/usbkill/
You can configure a whitelist of usb ids that are acceptable to insert and the remove.
The usb id can be found by running the command 'lsusb'.
Settings can be changed in local directory or /etc/usbkill/settings.ini

In order to be able to shutdown the computer, this program needs to run as root.
"""

def log(msg, lsusb=False):
    line = str(datetime.now()) + ' ' + msg
    print(line)

    if not log.path:
        return
    with open(log.path, 'a') as f:
        # Empty line to separate log enties
        f.write('\n')

        # Log the message that needed to be logged:
        f.write(line + '\n')

        # Log current usb state:
        if lsusb:
            f.write('Current state:\n')
    if lsusb:
        os.system("lsusb >> " + log.path)
log.path = None


def kill_computer(cfg):
    "Kill computer using buildin or external method"
    if cfg['simulate']:
        log("WARNING: Ignoring KILL procedure because of simulation mode")
        return

    # Log what is happening:
    if cfg['kill_cmd']:
        os.system(cfg['kill_cmd'])
        log("Kill script executed...")
        return

    # Buildin method of killing computer

    # Sync the filesystem so that the recent log entry does not get lost.
    os.system("sync")

    # Poweroff computer immediately
    if CURRENT_PLATFORM.startswith("DARWIN"):
        # OS X (Darwin) - Will reboot
        # Use Kernel Panic instead of shutdown command (30% faster and encryption keys are released)
        os.system("dtrace -w -n \"BEGIN{ panic();}\"")
    elif CURRENT_PLATFORM.endswith("BSD"):
        # BSD-based systems - Will shutdown
        os.system("shutdown -h now")
    else:
        # Linux-based systems - Will shutdown
        #os.system("poweroff -f")
        pass

    # Don't enter kill-loop
    log("Buildin kill executed")

def is_unlocked(cfg):
    "Check if screen/computer is unlocked"
    if not cfg['unlock_cmd']:
        return False
    ret = os.system(cfg['unlock_cmd'])
    if ret == 0:
        return True
    else:
        return False

def lsusb():
    "Return a list of connected devices on tracked BUSes"
    import glob
    devices = []
    if CURRENT_PLATFORM == "LINUX":
        path = '/sys/bus/usb/devices/*/idVendor'
        vendors = glob.glob(path)
        for entry in vendors:
            base = os.path.dirname(entry)
            vendor = open(os.path.join(base, 'idVendor')).read().strip()
            product = open(os.path.join(base, 'idProduct')).read().strip()
            device = vendor + ":" + product
            devices.append(device)
    else:
        df = subprocess.check_output("lsusb", shell=True).decode('utf-8')
        for line in df.split('\n'):
            if line:
                info = DEVICE_RE.match(line)
                if info:
                    dinfo = info.groupdict()
                    devices.append(dinfo['id'])
    return devices


def load_settings(filename):
    "Load settings from config file"
    # Load settings from local directory or global - if exists
    config = configparser.ConfigParser()
    config.read(['./settings.ini', SETTINGS_FILE])
    section = config['config']

    cfg = {
        'sleep_time': float(section['sleep']),
        'whitelist': [d.strip() for d in section['whitelist'].split(' ')],
        'kill_cmd': section['kill_cmd'],
        'unlock_cmd': section['unlock_cmd'],
        'kill_on_missing': int(section['kill_on_missing']),
        'log_file': section['log_file'],
    }
    return cfg


def loop(cfg):
    "Main loop"

    # Main loop that checks every 'sleep_time' seconds if computer should be killed.
    # Allows only whitelisted usb devices to connect!
    # Does not allow usb device that was present during program start to disconnect!
    known_devices = set(lsusb())

    # Write to logs that loop is starting:
    log("Started patrolling the USB ports every {0} seconds...".format(cfg['sleep_time']),
        lsusb=True)

    # Main loop
    while True:
        # List the current usb devices
        current_devices = set(lsusb())
        new_devices = current_devices - known_devices
        removed_devices = known_devices - current_devices

        # Check that all current devices are in the set of acceptable devices
        for device in new_devices:
            if device in cfg['whitelist']:
                log("INFO: New whitelisted device connected {0}".format(device), lsusb=True)
                known_devices.add(device)
                continue

            # New unknown device was connected
            if is_unlocked(cfg):
                log("INFO: New unknown device {0} connected while unlocked".format(device), lsusb=True)
                known_devices.add(device)
                continue

            # New unknown device connected while not unlocked.
            log("WARNING: New not-whitelisted device {0} detected - killing the computer...".format(device),
                lsusb=True)
            kill_computer(cfg)
            known_devices.add(device)

        # Check that all start devices are still present in current devices
        if removed_devices:
            desc = ", ".join(removed_devices)
            if is_unlocked(cfg):
                log("INFO: Device/s {0} disconnected while unlocked".format(desc))
                known_devices -= removed_devices
                continue

            # We are locked. And something got disconnected
            if cfg['kill_on_missing'] != 1:
                log("INFO: Device/s {0} disconnected but kill_on_missing disabled".format(desc))
                known_devices -= removed_devices
                continue

            log("WARNING: Device/s {0} disconnected while locked - killing the computer...".format(desc))

            kill_computer(cfg)
            known_devices -= removed_devices

        sleep(cfg['sleep_time'])

def exit_handler(signum, frame):
    log("Exiting because exit signal was received")
    sys.exit(0)


def test(cfg):
    "Test kill procedure"
    if is_unlocked(cfg):
        log("Device is currently unlocked (visible devices may change)")
    else:
        log("Device is locked (changes in visible devices cause a kill)")

    print()
    log("WARNING: Executing a test of a kill procedure in 10 seconds")
    sleep(5)
    log("5 seconds left... (Ctrl-C to cancel)")
    sleep(5)
    log("Executing a kill procedure")
    os.system('sync')
    kill_computer(cfg)

def main():
    "Check arguments and run program"
    import argparse
    p = argparse.ArgumentParser(description="usbkill", epilog=help_message)

    #p.add_argument("-h", "--help", dest="help",
    #               action="store_true",
    #               help="show help")

    p.add_argument("--test", dest="test",
                   action="store_true",
                   help="test kill and unlock procedure")

    p.add_argument("--simulate", dest="simulate",
                   action="store_true",
                   help="do everything, but don't kill device")
    args = p.parse_args()

    # Check if program is run as root, else exit.
    # Root is needed to power off the computer.
    if not os.geteuid() == 0:
        sys.exit("\nThis program needs to run as root.\n")

    # Register handlers for clean exit of loop
    for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT]:
        signal.signal(sig, exit_handler)

    # Load settings
    cfg = load_settings(SETTINGS_FILE)
    cfg['simulate'] = args.simulate

    log.path = cfg['log_file']

    log("Starting with whitelist: " + ",".join(cfg['whitelist']) )
    if args.simulate:
        log("WARNING: Simulation mode enabled")

    # Start main loop

    if args.test:
        test(cfg)
    else:
        loop(cfg)


if __name__=="__main__":
    main()
