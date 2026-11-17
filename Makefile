# Builds the .vsix by hand with zip, so Node and vsce aren't needed.
# Use another VS Code-based editor with: make install EDITOR_CLI=code

EDITOR_CLI ?= positron
VERSION := $(shell python3 -I -c "import json; print(json.load(open('package.json'))['version'])")
VSIX := build/outback-$(VERSION).vsix

.PHONY: install package theme check clean

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

# themes/outback.json is built from palette.toml and src/outback.json.
theme:
	python3 -I build.py

check:
	python3 -I build.py --check

clean:
	rm -rf build
