#!/usr/bin/env python

import argparse
import ConfigParser
import logging
import os
import paramiko
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
        '-a', 'x86_64', '-d', dist, 'rpm:all'
    ]
    logger.info("Building packages for %s", dist)
    logger.debug("Executing: %s", ' '.join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        stdout = process.stdout.readline()
        if stdout == '' and process.poll() is not None:
            break
        if stdout and debug:
            print stdout
    rc = process.poll()
    if rc != 0:
        logger.error("Failed to build packages, rc=%s", rc)
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

def sign_packages(packages):
    gpgpass = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.gpgpass')
    sign_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rpm-sign.exp')
    for p in packages:
        logger.info("GPG Signing %s", p)
        cmd = [sign_cmd, gpgpass, p]
        logger.debug("Executing: %s", ' '.join(cmd))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        exit_code = process.returncode
        if exit_code != 0:
            logger.error("GPG sign error: %s", out + err)
            return False
    return True

def release_packages(packages, host, path, pkey):
    _pkey = paramiko.RSAKey.from_private_key_file(pkey)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username='oodpkg', password=None, pkey=_pkey)
    sftp = ssh.open_sftp()
    for p in packages:
        f = os.path.basename(p)
        dest = os.path.join(path, f)
        logger.debug("SFTP %s -> oodpkg@%s:%s", p, host, dest)
        sftp.put(p, dest)
    sftp.close()
    ssh.close()

def update_repo(host, path, pkey):
    _pkey = paramiko.RSAKey.from_private_key_file(pkey)
    cmd = "cd %s ; createrepo_c ." % path
    logger.info("Updating repo metadata at %s:%s", host, path)
    logger.debug("Executing via SSH oodpkg@%s '%s'", host, cmd)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username='oodpkg', password=None, pkey=_pkey)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read()
    err = stderr.read()
    logger.debug("SSH CMD STDOUT:\n%s", out)
    logger.debug("SSH CMD STDERR:\n%s", err)
    ssh.close()

def run(passenger_root, cache_dir, output_dir, work_dir, rpm_host, rpm_path, srpm_host, srpm_path, dist, args):
    rpms, srpms = build_packages(passenger_root, cache_dir, output_dir, work_dir, dist, args.debug)
    if not rpms or not srpms:
        sys.exit(1)
    success = sign_packages(rpms)
    if not success:
        sys.exit(1)
    success = sign_packages(srpms)
    if not success:
        sys.exit(1)
    release_packages(rpms, rpm_host, rpm_path, args.pkey)
    release_packages(srpms, srpm_host, srpm_path, args.pkey)
    update_repo(rpm_host, rpm_path, args.pkey)
    update_repo(srpm_host, srpm_path, args.pkey)

def main():
    release_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.tito', 'releasers.conf')
    release_config = ConfigParser.ConfigParser()
    release_config.read(release_config_path)
    pkey = os.path.expanduser('~/.ssh/id_rsa')
    usage_examples = """
Usage examples:

    Build and release passenger and nginx RPMs
        %(prog)s

    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog=usage_examples)
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    parser.add_argument('-f', '--force', help='overwrite existing RPMs', action='store_true', default=False)
    parser.add_argument('--pkey', help='SSH private key to use for uploading RPMs', default=pkey)
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
    logging.getLogger('paramiko').setLevel(logging.WARNING)

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'passenger-release.ini')
    config = ConfigParser.ConfigParser()
    logger.debug("Loading config file %s", config_path)
    config.read(config_path)
    repo = config.get('main', 'repo')
    tag = config.get('main', 'tag')
    releases = config.get('main', 'releases').split(',')

    passenger_root = tempfile.mkdtemp()
    cache_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()
    work_dir = tempfile.mkdtemp()
    logger.debug("passenger=%s cache=%s output=%s work=%s", passenger_root, cache_dir, output_dir, work_dir)
    success = get_passenger(repo, tag, passenger_root)
    if not success:
        sys.exit(1)

    for release in releases:
        rpm_rsync = release_config.get(release, 'rsync')
        srpm_rsync = release_config.get("%s-source" % release, 'rsync')
        rpm_rsync_parts = rpm_rsync.split(':')
        rpm_host = rpm_rsync_parts[0]
        rpm_path = rpm_rsync_parts[1]
        srpm_rsync_parts = srpm_rsync.split(':')
        srpm_host = srpm_rsync_parts[0]
        srpm_path = srpm_rsync_parts[1]
        if 'el7' in release:
            dist = 'el7'
        elif 'el6' in release:
            dist = 'el6'
        else:
            logger.error("Unable to determine dist from release %s", release)
            sys.exit(1)
        logger.debug("rpm_rsync=%s srpm_rsync=%s dist=%s", rpm_rsync, srpm_rsync, dist)
        run(passenger_root, cache_dir, output_dir, work_dir, rpm_host, rpm_path, srpm_host, srpm_path, dist, args)

if __name__ == '__main__':
    main()
