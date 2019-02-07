#!/usr/bin/env python

import argparse
import ConfigParser
import logging
import os
import re
import subprocess
import sys
import tempfile


logger = logging.getLogger()


def get_passenger(repo, tag, root):
    logger.info("Git cloning passenger %s to %s", tag, root)
    clone_cmd = ['git', 'clone', '--branch', tag, repo, root]
    logger.debug("Executing %s", ' '.join(clone_cmd))
    process = subprocess.Popen(clone_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    exit_code = process.returncode
    if exit_code != 0:
        logger.error("Clone error: %s", out + err)
        return False
    subm_cmd = ['git', 'submodule', 'update', '--init', '--recursive']
    logger.debug("Executing %s", ' '.join(subm_cmd))
    process = subprocess.Popen(subm_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=root)
    out, err = process.communicate()
    exit_code = process.returncode
    if exit_code != 0:
        logger.error("Submodule error: %s", out + err)
        return False
    return True

def build_packages(passenger, cache, output, work, dist, debug):
    rpms = []
    srpms = []
    build_path = os.path.join(passenger, 'packaging/rpm', 'build')
    cmd = [
        build_path, '-p', passenger,
        '-c', cache, '-o', output, '-w', work,
        '-a', 'x86_64', '-d', dist, '-t', 'rpm:all'
    ]
    logger.info("Building packages for %s", dist)
    logger.debug("Executing: %s", ' '.join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        stdout = process.stdout.readline()
        if stdout == '' and process.poll() is not None:
            print stdout
            break
        if stdout and debug:
            print stdout
    rc = process.poll()
    if rc != 0:
        logger.error("Failed to build packages, rc=%s work=%s output=%s", rc, work, output)
        return False, False
    rpm_dir = os.path.join(output, dist)
    if not os.path.isdir(rpm_dir):
        logger.error("RPM Directory %s not found", rpm_dir)
        return False, False
    for f in os.listdir(rpm_dir):
        path = os.path.join(rpm_dir, f)
        if path.endswith('src.rpm'):
            logger.info("Found SRPM: %s", path)
            srpms.append(path)
        elif path.endswith('.rpm'):
            logger.info("Found RPM: %s", path)
            rpms.append(path)
    return rpms, srpms

def main():
    usage_examples = """
Usage examples:

    Build passenger and nginx RPMs
        %(prog)s --work /work --output /output --dist el7

    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog=usage_examples)
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    parser.add_argument('-w', '--work', required=True)
    parser.add_argument('-o', '--output', required=True)
    parser.add_argument('-D', '--dist', required=True)
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

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'passenger-nginx.ini')
    config = ConfigParser.ConfigParser()
    logger.debug("Loading config file %s", config_path)
    config.read(config_path)
    repo = config.get('main', 'repo')
    tag = config.get('main', 'tag')

    passenger_root = tempfile.mkdtemp(prefix='/tmp/')
    cache_dir = tempfile.mkdtemp(prefix='/tmp/')
    output_dir = args.output
    work_dir = args.work
    logger.debug("passenger=%s cache=%s output=%s work=%s", passenger_root, cache_dir, output_dir, work_dir)
    success = get_passenger(repo, tag, passenger_root)
    if not success:
        sys.exit(1)

    rpms, srpms = build_packages(passenger_root, cache_dir, output_dir, work_dir, args.dist, args.debug)
    if not rpms or not srpms:
        sys.exit(1)

if __name__ == '__main__':
    main()
