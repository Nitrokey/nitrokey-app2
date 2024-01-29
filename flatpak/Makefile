
MANIFEST=com.nitrokey.nitrokey-app2.yml


.PHONY: pkg run bundle clean lint check-meta full

pkg: $(MANIFEST)
	#flatpak-builder build $(MANIFEST) --force-clean
	flatpak run org.flatpak.Builder --force-clean --sandbox --user --install --install-deps-from=flathub --ccache --mirror-screenshots-url=https://dl.flathub.org/repo/screenshots --repo=repo builddir $(MANIFEST)

run:
	flatpak run com.nitrokey.nitrokey-app2

bundle:
	flatpak build-bundle repo nk-app2.flatpak com.nitrokey.nitrokey-app2

lint:
	flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest $(MANIFEST)
	flatpak run --command=flatpak-builder-lint org.flatpak.Builder repo repo

check-meta:
	flatpak run --command=appstream-util org.flatpak.Builder validate ../meta/com.nitrokey.nitrokey-app2.appdata.xml

clean:
	rm -f requirements.txt*
	rm -f pypi-dependencies.json
	rm -rf build venv builddir .flatpak-builder
	rm -rf flatpak-pip-generator
	rm -rf repo


requirements.txt: ../pyproject.toml
	cd .. && poetry export --without-hashes -f requirements.txt --output requirements.txt
	mv ../requirements.txt requirements.txt.raw
	sed -e '/hidapi/d' -e '/pyreadline3/d' -e '/pywin32/d' requirements.txt.raw > requirements.txt.raw2
	echo 'pyreadline3==3.4.1 ; python_version >= "3.9" and python_version < "3.12"' >> requirements.txt.raw2
	echo 'hidapi==0.14.0 ; python_version >= "3.9" and python_version < "3.12"' >> requirements.txt.raw2
	echo 'poetry==1.6.1 ; python_version >= "3.9" and python_version < "3.12"' >> requirements.txt.raw2
	echo 'poetry-core==1.7.0 ; python_version >= "3.9" and python_version < "3.12"' >> requirements.txt.raw2

	mv requirements.txt.raw2 requirements.txt

pypi-dependencies.json: requirements.txt flatpak-pip-generator
	python -m venv venv
	venv/bin/pip install requirements-parser
	venv/bin/python flatpak-pip-generator --runtime="org.kde.Sdk//6.6" --requirements-file="requirements.txt" --output pypi-dependencies
	# this might fail if there are multiple "org.kde.Sdk//6.6" installed (e.g. in user and system)
	# to fix: remove --user version like that: flatpak --user remove org.kde.Sdk


flatpak-pip-generator:
	curl https://raw.githubusercontent.com/flatpak/flatpak-builder-tools/master/pip/flatpak-pip-generator -o flatpak-pip-generator
	patch -p0 < flatpak-pip-generator.patch

full:
	-flatpak --user remove runtime/org.kde.Sdk/x86_64/6.6
	$(MAKE) clean
	$(MAKE) pypi-dependencies.json
	$(MAKE) 
