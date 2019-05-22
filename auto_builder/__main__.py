#!/usr/bin/env python3
from glob import glob
from pathlib import Path
from sh import Command, rsync, perl, grep
import argparse
import os
import requests
import sys


class BuildWatcher(object):
  def __init__(self):
    self.observed_build_failure = False

  def __call__(self, output, *args, **kwargs):
    print(output.strip())

    if 'FAILED' in output:
      self.observed_build_failure = True


def parse_args():
  parser = argparse.ArgumentParser(description='Build and release OnDemand RPMs.')

  sub_commands = parser.add_subparsers(dest='action')

  builder = sub_commands.add_parser(
    'build',
    help='Builds requested RPMs e.g. web/ondemand-bc_osc_matlab'
  )
  builder.add_argument(
    'rpms', nargs='+',
    help='List of RPMs to build'
  )

  releaser = sub_commands.add_parser(
    'release',
    help='Releases built RPMs stored in {}'.format(storage_dir()),
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  releaser.add_argument(
    '--pkey',
    help='An absolute path to your private key for the Yum server',
    type=Path,
    default=Path.home().joinpath('ClusterFS/.ssh/id_rsa')
  )

  args = parser.parse_args()

  if args.action is None:
    parser.print_help()
    exit(0)

  return args


def get_latest_release_tag(rpm):
  try:
    url = 'https://api.github.com/repos/osc/{}/releases/latest'.format(str(rpm).replace('ondemand-', '').replace('web/', ''))
    return requests.get(url).json()['tag_name']
  except Exception as e:
    print('Unable to get the latest release tag' + e)
    exit(1)


def bump_version_to_latest(rpm):
  version = get_latest_release_tag(rpm).replace('v', '')
  spec_file = rpm.joinpath('{}.spec'.format(rpm.name))
  print('Updating {} to version {}'.format(rpm, version))
  if str(rpm) == 'web/ondemand':
    handle_ondemand(version, spec_file)
  else:
    handle_regular(rpm, version, spec_file)


def handle_regular(rpm, version, spec_file):
  regex = r'Version: +\d+\.\d+\.\d+'
  new_version = 'Version:  {}'.format(version)

  perl(
    '-pi', '-e', 's[{}][{}]'.format(regex, new_version), spec_file,
    _out=sys.stdout, _err=sys.stderr
  )

  try:
    grep('-q', new_version, spec_file)
  except Exception as e:
    print('perl pie appears to have failed.')
    exit(1)


def handle_ondemand(version, spec_file):
  rpm = 'web/ondemand'
  try:
    versions = list(map(int, version.split('.')))
    if len(versions) == 2:
      versions.append(0)
    elif len(versions) != 3:
      raise ValueError()
  except ValueError:
    print('Error getting major, minor patch from {}'.format(version))
    exit(1)

  version_magntitudes = ('major', 'minor', 'patch')
  for version_magntitude, sub_version in zip(version_magntitudes, versions):
      regex = '{} [0-9]+'.format(version_magntitude)
      new_version = '{} {}'.format(version_magntitude, sub_version)
      perl(
        '-pi', '-e', 's[{}][{}]'.format(regex, new_version), spec_file,
        _out=sys.stdout, _err=sys.stderr
      )

      try:
        grep('-q', new_version, spec_file)
      except Exception as e:
        print('perl pie appears to have failed.')
        exit(1)


def build_rpm(rpm):
  # Remove this warning after handling release numbers
  print('#' + ('=' * 52) + '#')
  print('Note that the release number is currently not handled.')
  print('#' + ('=' * 52) + '#')

  bump_version_to_latest(rpm)
  build_sh = Command(Path(os.getcwd()).joinpath('build.sh'))
  rpm_path = Path(os.getcwd()).joinpath(rpm)

  if not rpm_path.is_dir():
    print("RPM spec {} does not exist at {}".format(rpm, rpm_path))
    exit(1)

  build_watcher = BuildWatcher()

  build_sh(
    '-w', '/tmp/work', '-o', '/tmp/output', rpm_path,
    _err_to_out=True,
    _out=build_watcher
  )

  if build_watcher.observed_build_failure:
    print('Build failed')
    exit(1)


def setup(storage_dir):
  storage_dir.mkdir(exist_ok=True)


def storage_dir():
  return Path(os.getcwd()).joinpath('built_rpms')


def run_build(rpms):

  setup(storage_dir())

  for rpm in rpms:
    print('Starting build of ' + rpm)
    build_rpm(Path(rpm))
    print('Copying output for {} to {}'.format(rpm, storage_dir()))

    rsync(
      # recursive, verbose, only updated files
      '-rvu', '/tmp/output/', storage_dir(),
      _out=sys.stdout, _err=sys.stderr
    )


def run_release(pkey):
  if not pkey.exists():
    print('Private key file not available at {}'.format(pkey))
    exit(1)

  release_script = Command(Path.cwd().joinpath('release.py'))
  release_script(
    '--pkey', pkey,
    glob('{}/*'.format(storage_dir())),
    _out=sys.stdout, _err=sys.stderr
  )


def main():
  args = parse_args()

  if args.action == 'build':
    run_build(args.rpms)
  elif args.action == 'release':
    run_release(args.pkey)

  print('Fin')


if __name__ == '__main__':
  main()