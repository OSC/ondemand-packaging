# OnDemand packaging

#### Table of Contents

1. [Requirements](#requirements)
1. [Install](#install)
1. [Usage - Rake Task](#usage---rake-task)
1. [Usage - CLI](#usage---cli)
1. [Create build box image](#create-build-box-image)
1. [Increment repo release](#increment-repo-release)
1. [Create release repo](#create-release-repo)
1. [Bootstrap latest release](#bootstrap-latest-release)
1. [Bootstrap build release](#bootstrap-build-release)

## Requirements

Builds are handled by [Docker](https://www.docker.com/get-started) or [podman](https://podman.io/).

## Install

To use the gem's built-in Rake tasks or CLI, include this in your Gemfile:

```
gem 'ood_packaging'
```

If you wish to only use the CLI tools, simply git clone this repo.

## Usage - Rake Task

To create a custom Rake task in another repo:

```ruby
require 'ood_packaging/rake_task

desc 'My OnDemand packaging Rake task'
OodPackaging::RakeTask.new(:package, [:dist]) do |t, args|
  t.package = Dir.pwd
  t.dist = args[:dist]
  t.tar = true
  t.version = ...
  t.work_dir = File.join('/tmp', ...)
  t.output_dir = File.join('/tmp', ...)
end
```

## Usage - CLI

If you install this repo via Gemfile replace `ood_package` with `bundle exec ood_package`.

If you clone this repo place `ood_package` with `./bin/ood_package`.

**NOTE: Replace `$DIST` with actual dist you wish to build against**

```
ood_package -w /tmp/work -o /tmp/output -d $DIST -V <VERSION HERE>
```

## Create build box image

Set `$DIST` to one of the supported dist values like `el8`

**NOTE: The official build images are created automatically upon a new release**

```
bundle exec rake ood_packaging:buildbox:build[$DIST]
```

## Publish RPMs (OSC)

If the ood_packaging `output_dir` was `/tmp/output` then the following command will upload the produced RPMs to the repo server:

```
./virtualenv/bin/python ./release.py /tmp/output/*
```

**CAUTION**: The `--force` flag is required if you wish to overwrite existing RPMs.

## Release RPMs

Build release RPMs:

```
rake ood_packaging:package:ondemand-release[el8]
rake ood_packaging:package:ondemand-release[ubuntu-20.04]
```

Release RPMs:

```
./virtualenv/bin/python ./release.py -c release ./tmp/output/*
```

## Compute RPMs

Build RPMs for compute:

```
rake ood_packaging:package:ondemand-compute[el8]
```

Release RPMs:

```
./virtualenv/bin/python ./release.py -c compute /tmp/output/*
```

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

This only has to be done once as `oodpkg` on OSC repo server

```
./sync-release.py --release latest
```

## Bootstrap build release

This only has to be done once as `oodpkg` on OSC repo server

```
./sync-release.py --release build/1.8
```

## Example using debmake to bootstrap deb files

```
docker run --rm -it -v $(pwd)/packages/deb/ondemand-release/build:/build ubuntu:20.04 /bin/bash
apt-get update
apt -y install debmake
cd /build
tar xf ondemand-release-1.tar.gz
cd ondemand-release-1
debmake -x 0
```

## Generate Deb GPG trust

```
docker run --rm -it --name ondemand-deb-gpg ubuntu:20.04 /bin/bash
apt-get update
apt -y install gnupg wget
wget -qO - https://apt.osc.edu/ondemand/DEB-GPG-KEY-ondemand | apt-key add -

# Back out of container
docker cp ondemand-deb-gpg:/etc/apt/trusted.gpg packages/deb/ondemand-release/ondemand.gpg
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
