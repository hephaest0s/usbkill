![usbkill](https://github.com/pwnsdx/usbkill/blob/master/Resources/USBKill.jpg?raw=true)

« usbkill » is a killswitch that wait for a change on your USB ports and then immediately shutdown your computer when there are. Anti-forensics.

> The project is still in early development stage but it does work and is effective. Expect improvements to come. Custom commands for when a USB change is observed will be implemented later.

To run:

```shell
sudo python3 usbkill.py
```

### Why?

Imagine your government comes busting in, or steals your laptop when you are at a public library (as with Ross). The police commonly use a « [mouse jiggler](http://www.amazon.com/Cru-dataport-Jiggler-Automatic-keyboard-Activity/dp/B00MTZY7Y4/ref=pd_bxgy_pc_text_y/190-3944818-7671348) » to keep the screensaver and sleep mode from activating.

If something like this happens to you, you would like to shutdown your computer immediately. This is what usbkill does.

Of course your government could be replaced by an adversary like a hacker or anyone else who want your informations.

> **Important**: Make sure to use full disk encryption! Otherwise they will get in anyway. 

> **Tip**: Additionally, you may use a cord to attach a usb key to your wrist. Then insert the key into your computer and start usbkill. If they steal your computer, the USB will be removed and the computer shuts down immediately.

### Note for OS X users

In order to work on OS X, you have to install *lsusb* port along with *python3* by using [brew](http://brew.sh):

```shell
brew update && \
brew tap jlhonora/lsusb && \
brew install python3 && \
brew install lsusb
```

### Contact

[hephaestos@riseup.net](mailto:hephaestos@riseup.net) - 8764 EF6F D5C1 7838 8D10 E061 CF84 9CE5 42D0 B12B


