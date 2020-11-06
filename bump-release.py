#!/usr/bin/env python

import argparse
import logging
import os
import re
import sys


logger = logging.getLogger()


def reset_version_release(spec_file, previous_version, new_version):
    with open(spec_file, 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if line.startswith('Version:'):
                m = re.search(r'^Version:(\s+)%s$' % previous_version, line)
                if not m:
                    f.write(line)
                    continue
                new_version = "Version:%s%s\n" % (m.group(1), new_version)
                logger.info("Modify %s version: old='%s' new='%s'", spec_file, line.strip(), new_version.strip())
                f.write(new_version)
            elif line.startswith('Release:'):
                m = re.search(r'^Release:(\s+)([\d]+)', line)
                if not m:
                    f.write(line)
                    continue
                if 'dist' in line:
                    new_release = "Release:%s1%%{?dist}\n" % m.group(1)
                else:
                    new_release = "Release:%s1\n" % m.group(1)
                logger.info("Modify %s release: old='%s' new='%s'", spec_file, line.strip(), new_release.strip())
                f.write(new_release)
            else:
                f.write(line)
        f.truncate()

def main():
    usage_examples = """
Usage examples:

    Sync given release
        %(prog)s --previous-release 1.3 --new-release 1.4

    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog=usage_examples)
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    parser.add_argument('-p', '--previous-release', required=True)
    parser.add_argument('-n', '--new-release', required=True)
    args = parser.parse_args()

    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logger.setLevel(log_level)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    repo_dir = os.path.dirname(__file__)

    specs_to_modify = [
        'packages/ondemand-compute/ondemand-compute.spec',
        'packages/ondemand-release/ondemand-release.spec',
        'packages/ondemand-runtime/ondemand-runtime.spec',
    ]
    files_to_modify = [
        'packages/ondemand-release/ondemand-compute.repo',
        'packages/ondemand-release/ondemand-web.repo',
        'packages/passenger/passenger.spec',
    ]
    for spec in specs_to_modify:
        reset_version_release(spec, args.previous_release, args.new_release)
    for _file in files_to_modify:
        with open(_file, 'r+') as f:
            lines = f.read()
            f.seek(0)
            logger.info("Modify %s replace %s with %s", _file, args.previous_release, args.new_release)
            new_lines = lines.replace(args.previous_release, args.new_release)
            f.write(new_lines)
            f.truncate()

if __name__ == '__main__':
    main()
