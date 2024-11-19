# Release Documentation

Follow the steps below meticulously to avoid a broken release.

1. Adapt version information.
   The CI pipeline will fail if the version strings in the files below do not match.
   * `nitrokeyapp/VERSION` (mind the final newline)
   * `pyproject.toml` 
   * `ci-scripts/linux/rpm/nitrokey-app2.spec` 
   * Add flatpak meta-data in `meta/com.nitrokey.nitrokey-app2.metainfo.xml`, 
     like this: `<release version="2.3" date="2024-04-19"/>` 
     * The latest release should be on top of this list.
2. Create a new tag and release.
   1. Make sure the `main` branch of your cloned repository is up-to-date.
      Create a new tag with `git tag -S -m "vX.Y.Z" vX.Y.Z` and push it to GitHub with `git push --tags`.
      Open the repository on GitHub and open the releases page.
      Click "Draft a new release" and select the just created tag.
   2. Open the repository on GitHub and open the releases page.
      Click "Draft a new release".
      In the dropdown field "Choose a tag" select "Create a new tag".
      Enter the version string in the form `vX.Y.Z`.
   Fill the fields title and description.
   Set the checkbox "Set as a pre-release" and create the release.
3. Wait for the pipelines to succeed.
   At this point the tag and release can still be removed.
4. Download the Windows artifacts ending in `_unsigned.exe` and `_unsigned.msi`.
   Sign the artifacts and remove the `_unsigned` from the file names.
   Open the release page for the version and click the edit button.
   Upload the signed artifacts and save the change.
5. Open the release page for the version and click the edit button.
   Change the release from pre-release to latest release and save the change.
6. Wait for the release pipelines to succeed.
7. Open the release page for the version and click the edit button.
   Remove the unsigned Windows binaries ending in `_unsigned.exe` and `_unsigned.msi` and save the change.
8. Please mind that Flatpak and RPM COPR builds need to be triggered manually.

The release is now complete.
