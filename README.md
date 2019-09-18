# OnDemand packaging

#### Table of Contents

1. [Requirements](#requirements)
1. [Install](#install)
1. [Create a new core package or dependency](#create-a-new-core-package-or-dependency)
1. [Update package](#update-package)
1. [Build and release Passenger and NGINX](#build-and-release-passenger-and-nginx)
1. [Increment repo release](#increment-repo-release)
1. [Create release repo](#create-release-repo)
1. [Build ondemand_buildbox Docker container](#build-ondemand_buildbox-docker-container)
1. [GPG Setup](#gpg-setup)
1. [Build RPM](#build-rpm)
1. [Publish RPMs (OSC)](#publish-rpms-osc)

## Requirements

Source files are referenced by git-annex.  Builds are handled by Docker.

* [git-annex](http://git-annex.branchable.com/)
* [docker](https://www.docker.com/get-started)
* [virtualenv](https://virtualenv.pypa.io/en/latest/)

## Install

Run:

* `git clone https://github.com/OSC/ondemand-packaging`
* `git annex init` to set up this repo for using git annex
* `./setup_sources.sh -D` to register git-annex file URLs
* `make`

## Create a new core package or dependency

For apps there is a bootstrap process that automates much of the initial setup.

1. Run: `./templates/mk_app_spec.sh <repo name> <app name> <version>`
  * Example: `./templates/mk_app_spec osc-systemstatus systemstatus 1.0.0`
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
4. Submit pull request to `master` branch

## Update package

1. Update spec file with new version
2. Change to package directory
3. Download source
  * `spectool -g -S example.spec`
4. Add the source to git annex by running
  * `git annex add example-2.0.0.tar.gz`
5. Remove old source
  * `git annex drop example-1.0.0.tar.gz`
  * `git rm example-1.0.0.tar.gz`
6. Build [Build RPM](#build-rpm)
7. Commit changes
8. Release Package [Publish RPMs (OSC)](#publish-rpms-osc)

## Build and release Passenger and NGINX

1. Ensure `passenger-release.ini` has the correct value for `tag`.
2. Run the build script:
  * `./build.sh -w /tmp/work -o /tmp/output -t build:passenger_nginx $(pwd)/build/passenger-nginx.py`
3. Publish RPMs (OSC)
  * `./release.py /tmp/output/*`

The script for passenger performs the following steps:
* Clone passenger git repo using specified git `tag` value
* Build passenger and nginx RPMs
* GPG Sign RPMs and SRPMs
* SFTP upload signed RPMs and SRPMs to repo server
* Update repo metadata

## Increment repo release

This step will be done after a release branch is created. For example, after `1.3` branch is created this workflow would be performed to stage master for future `1.4` work.

1. Ensure on the `master` branch
2. Run `bump-release.py`, example going from `1.3` to `1.4`
  * `./bump-release.py -p 1.3 -n 1.4`
3. Build RPMs for each updated package using one build command - [Build RPM](#build-rpm)
4. Release Packages [Publish RPMs (OSC)](#publish-rpms-osc)

## Create release repo

A release repo would be created after when it's time to release OnDemand 1.3, for example.

1. Create 1.3 branch of this repo from master
2. Ensure release-manifest.yaml is up-to-date with desired package versions
3. As `oodpkg` user from OSC repo server, run `sync-release.py`
  * `./sync-release.py --release 1.3`
  * NOTE: Run with `--force` if existing RPMs need to be overwritten, which should be rare
  * NOTE: Run with `--clean` if RPMs need to be removed from release repo
4. In `master` branch bump OnDemand release specific packages
  * See [Increment repo release](#increment-repo-release)

Any changes that need to be made to package versions after a release repo is created will be done by repeating steps #3 and #4 from above.

## Bootstrap latest release

This only has to be done once

```
./sync-release.py --release latest
```

## Build ondemand_buildbox Docker container

```
cd docker-image
rm mock-cache.tar.gz
docker build -t ohiosupercomputer/ondemand_buildbox:0.0.1 .
# update build/env
./make-mock-cache.sh
docker build --no-cache -t ohiosupercomputer/ondemand_buildbox:0.0.1 .
docker push ohiosupercomputer/ondemand_buildbox:0.0.1
```

## GPG Setup

First create a GPG public and private key.  This should only be done once.  The passphrase used should be saved to `.gpgpass` file and `ondemand.sec` file saved to root of this repo.  The `ondemand.pub` will be needed by anyone wishing to install the GPG signed packages.

```
cat > gen <<EOF
Key-Type: RSA
Key-Length: 2048
Key-Usage: encrypt
Subkey-Type: RSA
Subkey-Length: 2048
Subkey-Usage: encrypt
Name-Real: My Site Key
Name-Email: packages@example.com
Expire-Date: 0
%pubring ondemand.pub
%secring ondemand.sec
%commit
%echo done
EOF

gpg --gen-key --batch gen
```

Substitute `Name-Real` and `Name-Email` with site specific values.  The value of `Name-Real` needs to be passed to `build.sh` at build time via the `-G` flag.

## Build RPM

Builds are performed using Docker.

The following example will build an RPM for CentOS/RHEL 7.  The RPMs will be written to /tmp/output/el7 and signed by GPG key named 'My Site Key'.  The files `.gpgpass` and `ondemand.sec` must exist at the root of this repo if you wish to perform GPG signing. The value for `-g` must point to path to GPG public key.

```
./build.sh -w /tmp/work -o /tmp/output -d el7 -G 'My Site Key' -g /path/to/GPG-pubkey /path/to/app/directory/with/spec
```

The last argument is the path to a directory holding spec file for the package you wish to build.

If there are errors during build you can either check under the path for `-w` or build with `-A` flag.  If you build with `-A` flag you are given a shell after all builds.

```
./build.sh -w /tmp/work -o /tmp/output -d el7 -G 'My Site Key' -g /path/to/GPG-pubkey -A /path/to/app/directory/with/spec
```

## Publish RPMs (OSC)

If `./build.sh` had `-o /tmp/output` then the following command will upload the produced RPMs to the repo server:

```
./virtualenv/bin/python ./release.py /tmp/output/*
```

**CAUTION**: The `--force` flag is required if you wish to overwrite existing RPMs.

## Release RPMs

Build release RPMs:

```
./build.sh -w /tmp/work -o /tmp/output -d el7 -S $(pwd)/misc/ondemand-release
```

Release RPMs:

```
./virtualenv/bin/python ./release.py -c release /tmp/output/*
```

## Compute RPMs

Build RPMs for compute:

```
./build.sh -w /tmp/work -o /tmp/output -S $(pwd)/compute/ondemand-compute
```

Release RPMs:

```
./virtualenv/bin/python ./release.py -c compute /tmp/output/*
```
