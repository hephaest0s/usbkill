![usbkill](Resources/USBKillBanner.jpg)

« usbkill » is an anti-forensic kill-switch that waits for a change on your USB ports and then immediately shuts down your computer.

> The project is still under development but it does work and is effective. Expect improvements to come. Custom commands for when a USB change is observed will be implemented.

To run:

```shell
sudo python3 usbkill.py
```

### Why?

There are 3 reasons (maybe more?) to use this tool:

- In case the police or other thugs come busting in (or steal your laptop from you when you are at a public library as happened to Ross). The police commonly uses a « [mouse jiggler](http://www.amazon.com/Cru-dataport-Jiggler-Automatic-keyboard-Activity/dp/B00MTZY7Y4/ref=pd_bxgy_pc_text_y/190-3944818-7671348) » to keep the screensaver and sleep mode from activating.
- You don't want someone to install backdoors or malware on your computer or to retrieve documents from your computer via USB.
- You want to improve the security of your (Full Disk Encrypted) home or corporate server (e.g. Your Raspberry).

> **[!] Important**: Make sure to use full disk encryption! Otherwise they will get in anyway. 

> **Tip**: Additionally, you may use a cord to attach a USB key to your wrist. Then insert the key into your computer and start usbkill. If they steal your computer, the USB will be removed and the computer shuts down immediately.

### Additional requirement for OS X users

In order to make usbkill work on OS X, you have to install *python3* by using [brew](http://brew.sh):

```shell
brew update && brew install python3
```

### Contact

[hephaestos@riseup.net](mailto:hephaestos@riseup.net) - PGP/GPG Fingerprint: 8764 EF6F D5C1 7838 8D10 E061 CF84 9CE5 42D0 B12B


