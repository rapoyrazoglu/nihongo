PREFIX ?= /usr/local
BINDIR  = $(PREFIX)/bin
ICONDIR = $(PREFIX)/share/icons/hicolor/scalable/apps
APPDIR  = $(PREFIX)/share/applications

.PHONY: build install uninstall

build:
	bash build.sh

install: dist/nihongo
	install -Dm755 dist/nihongo       $(DESTDIR)$(BINDIR)/nihongo
	install -Dm644 assets/nihongo.svg $(DESTDIR)$(ICONDIR)/nihongo.svg
	install -Dm644 nihongo.desktop    $(DESTDIR)$(APPDIR)/nihongo.desktop
	@echo "Kurulum tamam: $(BINDIR)/nihongo"

uninstall:
	rm -f $(DESTDIR)$(BINDIR)/nihongo
	rm -f $(DESTDIR)$(ICONDIR)/nihongo.svg
	rm -f $(DESTDIR)$(APPDIR)/nihongo.desktop
	@echo "Kaldırıldı."
