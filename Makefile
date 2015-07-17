PREFIX = /usr/local
BINPREFIX = $(PREFIX)/bin
MANPREFIX = $(PREFIX)/share/man
ETCPREFIX = $(PREFIX)/etc/usbkill

install:
	cp usbkill.py $(BINPREFIX)/usbkill.py
	mkdir -p $(ETCPREFIX)
	cp settings.ini $(ETCPREFIX)/settings.ini

uninstall:
	rm -rf $(BINPREFIX)/usbkill.py
	rm -rf $(ETCPREFIX)
