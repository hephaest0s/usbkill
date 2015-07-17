PREFIX = /usr/local
BINPREFIX = $(PREFIX)/bin
MANPREFIX = /usr/share/man
ETCPREFIX = $(PREFIX)/etc/usbkill

install:
	cp usbkill.py $(BINPREFIX)/usbkill.py
	mkdir -p $(ETCPREFIX)
	cp settings.ini $(ETCPREFIX)/settings.ini
	cp doc/man1/usbkill.1 $(MANPREFIX)/man1/
	cp doc/man5/usbkill-settings.ini.5 $(MANPREFIX)/man5/

uninstall:
	rm -rf $(BINPREFIX)/usbkill.py
	rm -rf $(ETCPREFIX)
	rm -rf $(MANPREFIX)/man1/usbkill.1
	rm -rf $(MANPREFIX)/man/usbkill-settings.ini.5
