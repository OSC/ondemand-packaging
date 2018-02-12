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

* `git clone https://github.com/OSC/ood-packaging -b develop`
* `git annex init` to set up this repo for using git annex
* `./setup_sources.sh` to register git-annex file URLs

## HOWTO: test a package

Before tagging a build, please test it.  Using tito's --test flag, you can
generate test (S)RPMs by first committing your changes locally, then it will
use the SHA in the RPM version.

### With mock

Configuration for mock is supplied in mock/ and can be used to build any of
the packages locally and quickly.

```
tito build --rpm --test --builder tito.builder.MockBuilder --arg mock_config_dir=mock/ --dist=.el7 --arg mock=el7-nonscl
```

The last argument is the name of the mock config in mock/, which includes SCL
and non-SCL variants.  Anything under the `web` directory will require the scl configuration like `el7-scl`.

**Notice:** tito works only on committed changes! If you are changing the `.spec` files, make sure you commit those changes before running `tito build` command.

## HOWTO: create a new core package or dependency

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

## HOWTO: release package

1. Tag package after changing to package directory:
  * `tito tag --keep-version`
2. Release package
  * `RSYNC_USERNAME=mirror tito release --all-starting-with=web-scl`
  * The value for `--all-starting-with` varies based on parent directory of package directory
    * `compute` - Use `compute`
    * `web-nonscl` - Use `web-nonscl`
    * `web` - Use `web-scl`
    * `misc/ood-release` - Use `release`

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
