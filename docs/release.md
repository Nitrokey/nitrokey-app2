# Release Documentation

* adapt version information (todo: centralize)

  * `/VERSION` (mind the final newline)
  * `pyproject.toml` 
  * `ci-scripts/linux/rpm/nitrokey-app2.spec` 
  * `flatpak` (todo) 

* create tag (`git tag -S -m "vX.Y.Z" vX.Y.Z` or in the web-ui)

* `git push --tags`

* create release based on tag (web-ui)

  * set `pre-release` if required...

* wait for actions to fail
