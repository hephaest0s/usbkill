![usbkill](Resources/USBKillBanner.gif)

« usbkill » is an anti-forensic kill-switch that waits for a change on your USB ports and then immediately shuts down your computer.

To run:

```shell
sudo python usbkill.py
```
or
```shell
sudo python3 usbkill.py
```

Related project; same idea, but implemented as a Linux driver: https://github.com/NateBrune/silk-guardian


### Why?

Some reasons to use this tool:

- In case the police or other thugs come busting in (or steal your laptop from you when you are at a public library, as happened to Ross). The police commonly uses a « [mouse jiggler](http://www.amazon.com/Cru-dataport-Jiggler-Automatic-keyboard-Activity/dp/B00MTZY7Y4/ref=pd_bxgy_pc_text_y/190-3944818-7671348) » to keep the screensaver and sleep mode from activating.
- You don’t want someone to add or copy documents to or from your computer via USB.
- You want to improve the security of your (encrypted) home or corporate server (e.g. Your Raspberry).

> **[!] Important**: Make sure to use disk encryption for all folders that contain information you want to be private. Otherwise they will get it anyway. Full disk encryption is the easiest and surest option if available

> **Tip**: Additionally, you may use a cord to attach a USB key to your wrist. Then insert the key into your computer and start usbkill. If they steal your computer, the USB will be removed and the computer shuts down immediately.

### Feature List
(version 1.0-rc.4)
- Compatible with Linux, *BSD and OS X.
- Shutdown the computer when there is USB activity.
- Customizable. Define which commands should be executed just before shut down.
- Ability to whitelist a USB device.
- Ability to change the check interval (default: 250ms).
- Ability to melt the program on shut down.
- RAM and swap wiping.
- Works with sleep mode (OS X).
- No dependency except secure-delete iff you want usbkill to delete files/folders for you or if you want to wipe RAM or swap. ```sudo apt-get install secure-delete```
- Sensible defaults


### Supported command line arguments (partially for devs):

- -h or --help: show help message, exit.
- --version: show version of the program, exit.
- --no-shut-down: if a malicious change on the USB ports is detected, execute all the (destructive) commands you defined in settings.ini, but don’t turn off the computer.
- --cs: Copy program folder settings.ini to /etc/usbkill/settings.ini

### Contact

[hephaestos@riseup.net](mailto:hephaestos@riseup.net) - PGP/GPG Fingerprint: 8764 EF6F D5C1 7838 8D10 E061 CF84 9CE5 42D0 B12B

