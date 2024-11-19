# Release Documentation

* adapt version information (todo: centralize)

  * `/VERSION` (mind the final newline)
  * `pyproject.toml` 
  * `ci-scripts/linux/rpm/nitrokey-app2.spec` 
  * add flatpak meta-data in `meta/com.nitrokey.nitrokey-app2.metainfo.xml`, 
    like this: `<release version="2.3" date="2024-04-19"/>` 
    * the latest release should be on top of this list


* create tag (`git tag -S -m "vX.Y.Z" vX.Y.Z` or in the web-ui)

* `git push --tags`

* create release based on tag (web-ui)

  * set `pre-release` if required...

* wait for actions to fail
