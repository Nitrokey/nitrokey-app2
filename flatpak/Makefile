
MANIFEST=com.nitrokey.nitrokey-app2.yml


pkg: pypi-dependencies.json $(MANIFEST)
	flatpak-builder build $(MANIFEST) --force-clean

user: pypi-dependencies.json $(MANIFEST)
	flatpak-builder build $(MANIFEST) --force-clean --user --install

run:
	flatpak run com.nitrokey.nitrokey-app2

clean:
	rm -f requirements.txt*
	rm -f pypi-dependencies.json
	rm -rf build venv
	rm -rf flatpak-pip-generator

.PHONY: user pkg run clean


requirements.txt: ../pyproject.toml
	cd .. && poetry export --without-hashes -f requirements.txt --output requirements.txt
	mv ../requirements.txt requirements.txt.raw
	sed -e '/hidapi/d' -e '/pyreadline3/d' -e '/pywin32/d' requirements.txt.raw > requirements.txt.raw2
	echo 'pyreadline3==3.4.1 ; python_version >= "3.9" and python_version < "3.12"' >> requirements.txt.raw2
	echo 'hidapi==0.14.0 ; python_version >= "3.9" and python_version < "3.12"' >> requirements.txt.raw2
	echo 'poetry==1.6.1 ; python_version >= "3.9" and python_version < "3.12"' >> requirements.txt.raw2
	mv requirements.txt.raw2 requirements.txt

pypi-dependencies.json: requirements.txt flatpak-pip-generator
	python -m venv venv
	venv/bin/pip install requirements-parser
	venv/bin/python flatpak-pip-generator --runtime="org.kde.Sdk//6.6" --requirements-file="requirements.txt" --output pypi-dependencies

flatpak-pip-generator:
	curl https://raw.githubusercontent.com/flatpak/flatpak-builder-tools/master/pip/flatpak-pip-generator -o flatpak-pip-generator
	patch -p0 < flatpak-pip-generator.patch

