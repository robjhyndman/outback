# Builds the .vsix by hand with zip, so Node and vsce aren't needed.
# Use another VS Code-based editor with: make install EDITOR_CLI=code

EDITOR_CLI ?= positron
VERSION := $(shell python3 -I -c "import json; print(json.load(open('package.json'))['version'])")
VSIX := build/outback-$(VERSION).vsix

.PHONY: install package theme extras install-extras install-zen check clean

install: package
	$(EDITOR_CLI) --install-extension $(VSIX) --force
	@echo "Installed. Run 'Developer: Reload Window' to see the changes."

package: theme
	rm -rf build
	mkdir -p build/vsix/extension
	cp -r package.json README.md LICENSE THIRD_PARTY_NOTICES.md themes syntaxes build/vsix/extension/
	cp 'packaging/[Content_Types].xml' build/vsix/
	sed 's/@VERSION@/$(VERSION)/' packaging/extension.vsixmanifest.in > build/vsix/extension.vsixmanifest
	cd build/vsix && zip -qr -X ../outback-$(VERSION).vsix '[Content_Types].xml' extension.vsixmanifest extension

# themes/outback.json is built from palette.toml and src/outback.json,
# and the themes for other apps in extras/ from those two.
theme:
	python3 -I build.py
	python3 -I extras.py

extras: theme

# Symlink the extras where each app looks for them, so a pull and rebuild updates them.
CONFIG := $(or $(XDG_CONFIG_HOME),$(HOME)/.config)
DATA   := $(or $(XDG_DATA_HOME),$(HOME)/.local/share)
LINKS  := zed/outback.json:$(CONFIG)/zed/themes/outback.json \
          konsole/Outback.colorscheme:$(DATA)/konsole/Outback.colorscheme \
          kde/Outback.colors:$(DATA)/color-schemes/Outback.colors \
          bat/Outback.tmTheme:$(CONFIG)/bat/themes/Outback.tmTheme \
          eza/theme.yml:$(CONFIG)/eza/theme.yml \
          rstudio/Outback.rstheme:$(CONFIG)/rstudio/themes/Outback.rstheme

install-extras:
	@for l in $(LINKS); do \
	  src=$(CURDIR)/extras/$${l%%:*}; dst=$${l#*:}; \
	  mkdir -p "$$(dirname "$$dst")" && ln -sfn "$$src" "$$dst" && echo "linked $$dst"; \
	done
	@dst="$(CONFIG)/sublime-merge/Packages/User"; mkdir -p "$$dst"; \
	 for src in "$(CURDIR)"/extras/sublime-merge/*; do \
	   ln -sfn "$$src" "$$dst/$${src##*/}" && echo "linked $$dst/$${src##*/}"; \
	 done
	@bat=$$(command -v batcat || command -v bat); \
	 if [ -n "$$bat" ]; then "$$bat" cache --build >/dev/null && echo "rebuilt bat's theme cache"; fi
	@$(MAKE) --no-print-directory install-zen

# Zen keeps userChrome.css in its default profile, whose folder name is random:
# installs.ini names the profile this install uses, else profiles.ini's Default=1.
# Zen moved its profiles from ~/.zen to ~/.config/zen, so the first folder found wins.
ZEN_DIRS := $(HOME)/.var/app/app.zen_browser.zen/config/zen $(CONFIG)/zen \
            $(HOME)/.var/app/app.zen_browser.zen/.zen $(HOME)/.zen

install-zen:
	@for d in $(ZEN_DIRS); do \
	  [ -f "$$d/profiles.ini" ] || continue; \
	  p=$$(awk -F= '$$1 == "Default" { print $$2; exit }' "$$d/installs.ini" 2>/dev/null); \
	  [ -n "$$p" ] || p=$$(awk -F= '/^\[/ { path = "" } $$1 == "Path" { path = $$2 } \
	    $$1 == "Default" && $$2 == "1" && path != "" { print path; exit }' "$$d/profiles.ini"); \
	  [ -n "$$p" ] || continue; \
	  case "$$p" in /*) prof="$$p" ;; *) prof="$$d/$$p" ;; esac; \
	  mkdir -p "$$prof/chrome" && ln -sfn "$(CURDIR)/extras/zen/userChrome.css" "$$prof/chrome/userChrome.css" && \
	    echo "linked $$prof/chrome/userChrome.css"; \
	  if [ -e "$$prof/user.js" ] && [ ! -L "$$prof/user.js" ]; then \
	    echo "$$prof/user.js exists; add the line in extras/zen/user.js to it"; \
	  else ln -sfn "$(CURDIR)/extras/zen/user.js" "$$prof/user.js" && echo "linked $$prof/user.js"; fi; \
	  echo "restart Zen to see the changes"; break; \
	done

check:
	python3 -I build.py --check
	python3 -I extras.py --check

clean:
	rm -rf build
