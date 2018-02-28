# OnDemand packaging

This repositories branches contain RPM spec files for OnDemand's dependencies and core applications.

## Requirements

Source files are referenced by git-annex.  Builds are handled by tito and mock.

* [git-annex](http://git-annex.branchable.com/)
* [tito](https://github.com/dgoodwin/tito) 0.6.1 or higher
* [mock](http://fedoraproject.org/wiki/Projects/Mock)
* scl-utils-build package (Fedora or Red Hat repositories)

## HOWTO: checkout

Run:

* `git clone https://github.com/OSC/ondemand-packaging -b develop`
* `git annex init` to set up this repo for using git annex
* `./setup_sources.sh` to register git-annex file URLs

## HOWTO: test a package

Before tagging a build, please test it.  Using tito's --test flag, you can
generate test (S)RPMs by first committing your changes locally, then it will
use the SHA in the RPM version.

### With mock

Configuration for mock is supplied in mock/ and can be used to build any of
the packages locally and quickly.

```sh
tito build --rpm --test --builder tito.builder.MockBuilder --output $(mktemp -d) --arg mock_config_dir=mock/ --dist=.el7 --arg mock=el7-scl
```

The last argument is the name of the mock config in mock/, which includes SCL
and non-SCL variants.  If SCL is not needed for the build then use `el7-nonscl`.

**Notice:** tito works only on committed changes! If you are changing the `.spec` files, make sure you commit those changes before running `tito build` command.

## HOWTO: create a new core package or dependency

For apps there is a bootstrap process that automates much of the initial setup.

1. Run: `./mk_app_spec.sh <repo name> <app name> <version>`
2. Update description and summary and adjust build and install dependencies

Manually adding spec file:

1. Add the spec to a subdirectory under one of the following directories
  * compute - packages intended for compute nodes
  * web-nonscl - packages for web host that do not require SCL
  * web - packages for web host that do require SCL
  * misc - anything that doesn't fit into one of the above items
2. Download source by running:
  * `spectool -g -S example.spec`
3. Add the source to git annex by running:
  * `git annex add example-1.0.0.tar.gz`
4. Submit pull request to `develop` branch

## HOWTO: Update package

1. Update spec file with new version
2. Change to package directory
3. Download source
  * `spectool -g -S example.spec`
4. Add the source to git annex by running
  * `git annex add example-2.0.0.tar.gz`
5. Remove old source
  * `git annex drop example-1.0.0.tar.gz`
  * `git rm example-1.0.0.tar.gz`
6. Commit changes
7. Test build [HOWTO: test a package](#howto-test-a-package)
8. Release Package [HOWTO: release package](#howto-release-package)

## HOWTO: release package

1. Tag package after changing to package directory:
  * `tito tag --keep-version`
2. Push new tag and commit to origin
  * `git push --tags origin master`
3. Go back to root of this repo:
  * `cd ../..`
3. Release package
  * `./release.sh <spec directory(s)>`
  * Example: `./release.sh web/ondemand-bc_osc_abaqus`
  * Example wildcard: `./release.sh web/ondemand-*`
  * Manual:
    * `RSYNC_USERNAME=oodpkg tito release --all-starting-with=web-scl`
    * The value for `--all-starting-with` varies based on parent directory of package directory
      * `compute` - Use `compute`
      * `web-nonscl` - Use `web-nonscl`
      * `web` - Use `web-scl`
      * `misc/ondemand-release` - Use `release`
      * `web/mod_auth_openidc` - Use `web-httpd24`

## How does this repo work?

This repo contains a directory per source package and some tito configuration
and state (under .tito/).  Each source package directory contains a spec
file and patches under version control plus references to the source files
(i.e. tarballs).

These references are managed using git-annex, a git extension for tracking
large binary blobs outside of the git repo itself.  This means we can
reference source files directly on rubygems.org etc, or perhaps set up a kind
of lookaside cache in the future.  For now, we use the [special web remote](http://git-annex.branchable.com/tips/using_the_web_as_a_special_remote/)
with URLs to all of our source files available on the web.

tito's git-annex support will automatically (lazily) fetch files and cache
them in your local git checkout as and when you build packages.

tito works in two key stages: tagging and releasing.  For every RPM build, a
tag needs to be created with tito (i.e. `tito tag --keep-version`) and this
git tag is pushed to the central repository.  tito helps by creating a
%changelog entry and tags in standard formats etc.

When a tag is present in the central repository for a version, tito lets you
build a SRPM and submit to koji, which builds the binary package (whereupon it
gets pulled into our yum repositories).  This tagging strategy means we can
rebuild a package from any point in the repository's history, and since the
git-annex metadata is part of the tagged commit, even the binary content is
effectively under source control.

This repository is branched for major releases.

## Support GPG signing

Two files must be setup.  The local GPG keyring must have both private and public keys used by OnDemand.  Once the GPG keyring has key imported setup `~/.rpmmacros`

```
cat > ~/.rpmmacros <<EOF
%_signature gpg
%_gpg_path $HOME/.gnupg
%_gpg_name OnDemand Release Signing Key
%_gpg /usr/bin/gpg
EOF
```

Next the private key passphrase needs to be added to `.gpgpass` under this repo.
