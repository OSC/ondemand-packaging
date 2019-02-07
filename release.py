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


def release_packages(packages, host, path, pkey, force):
    uploads = False
    _pkey = paramiko.RSAKey.from_private_key_file(pkey)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username='oodpkg', password=None, pkey=_pkey)
    sftp = ssh.open_sftp()
    files = sftp.listdir(path)
    for p in packages:
        f = os.path.basename(p)
        if f in files and not force:
            logger.info("SKIPPING %s: Exists at %s:%s", f, host, path)
            continue
        dest = os.path.join(path, f)
        logger.debug("SFTP %s -> oodpkg@%s:%s", p, host, dest)
        sftp.put(p, dest)
        uploads = True
    sftp.close()
    ssh.close()
    return uploads

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

def main():
    pkey = os.path.expanduser('~/.ssh/id_rsa')
    usage_examples = """
Usage examples:

    Release RPMs
        %(prog)s /tmp/output

    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog=usage_examples)
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    parser.add_argument('-f', '--force', help='overwrite existing RPMs', action='store_true', default=False)
    parser.add_argument('--pkey', help='SSH private key to use for uploading RPMs (default: %(default)s)', default=pkey)
    parser.add_argument('dirs', nargs='+')
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

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'release.ini')
    config = ConfigParser.ConfigParser()
    logger.debug("Loading config file %s", config_path)
    config.read(config_path)
    host = config.get('main', 'host')

    for release_dir in args.dirs:
        dist = os.path.basename(release_dir)
        rpm_path = config.get('main', 'rpm_path').replace('DIST', dist)
        srpm_path = config.get('main', 'srpm_path').replace('DIST', dist)
        logger.debug("rpm_path=%s srpm_path=%s dist=%s", rpm_path, srpm_path, dist)
        rpms = []
        srpms = []
        for f in os.listdir(release_dir):
            p = os.path.join(release_dir, f)
            if p.endswith('.src.rpm'):
                logger.debug("Found SRPM: %s", p)
                srpms.append(p)
            elif p.endswith('.rpm'):
                logger.debug("Found RPM: %s", p)
                rpms.append(p)
        rpms_released = release_packages(rpms, host, rpm_path, args.pkey, args.force)
        srpms_released = release_packages(srpms, host, srpm_path, args.pkey, args.force)
        if rpms_released:
            update_repo(host, rpm_path, args.pkey)
        if srpms_released:
            update_repo(host, srpm_path, args.pkey)

if __name__ == '__main__':
    main()
