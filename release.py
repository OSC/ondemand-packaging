#!/usr/bin/env python

import argparse
try:
    import ConfigParser
except ModuleNotFoundError:
    import configparser as ConfigParser
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
        logger.info("Release: %s to %s", p, dest)
        sftp.put(p, dest)
        uploads = True
    sftp.close()
    ssh.close()
    return uploads

def update_repo(host, path, pkey, gpgpass):
    _pkey = paramiko.RSAKey.from_private_key_file(pkey)
    with open(gpgpass, 'r') as f:
        gpg_passphrase = f.read().strip()
    createrepo_cmd = "cd %s ; createrepo_c --update ." % path
    gpg_cmd = "cd %s ; gpg --detach-sign --passphrase %s --batch --yes --no-tty --armor repodata/repomd.xml" % (path, gpg_passphrase)
    logger.info("Updating repo metadata at %s:%s", host, path)
    logger.debug("Executing via SSH oodpkg@%s '%s'", host, createrepo_cmd)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username='oodpkg', password=None, pkey=_pkey)
    createrepo_stdin, createrepo_stdout, createrepo_stderr = ssh.exec_command(createrepo_cmd)
    createrepo_out = createrepo_stdout.read()
    createrepo_err = createrepo_stderr.read()
    logger.debug("SSH CMD STDOUT:\n%s", createrepo_out)
    logger.debug("SSH CMD STDERR:\n%s", createrepo_err)
    logger.debug("Executing via SSH oodpkg@%s '%s'", host, gpg_cmd)
    gpg_stdin, gpg_stdout, gpg_stderr = ssh.exec_command(gpg_cmd)
    gpg_out = gpg_stdout.read()
    gpg_err = gpg_stderr.read()
    logger.debug("SSH CMD STDOUT:\n%s", gpg_out)
    logger.debug("SSH CMD STDERR:\n%s", gpg_err)
    ssh.close()

def main():
    pkey = os.path.expanduser('~/.ssh/id_rsa')
    gpgpass = os.path.join(os.path.dirname(__file__), '.gpgpass')
    usage_examples = """
Usage examples:

    Release RPMs
        %(prog)s /tmp/output/*

    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog=usage_examples)
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    parser.add_argument('-f', '--force', help='overwrite existing RPMs', action='store_true', default=False)
    parser.add_argument('--pkey', help='SSH private key to use for uploading RPMs (default: %(default)s)', default=pkey)
    parser.add_argument('-g','--gpgpass', help='GPG passphrase file (default: %(default)s)', default=gpgpass)
    parser.add_argument('-c', '--config-section', help='config section to use', default='main')
    parser.add_argument('-r', '--release', help='Build repo release to use', default=None)
    parser.add_argument('dirs', nargs='+')
    args = parser.parse_args()

    if args.config_section == 'build' and args.release is None:
        print("ERROR: config-section build requires -r/--release flag")
        sys.exit(1)

    if args.release is not None:
        release_bits = args.release.replace('v', '').split('.')
        build_release = "%s.%s" % (release_bits[0], release_bits[1])
    else:
        build_release = ''

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
    update = config.getboolean(args.config_section, 'update')

    for release_dir in args.dirs:
        dist = os.path.basename(release_dir)
        rpm_path = config.get(args.config_section, 'rpm_path').replace('DIST', dist).replace('RELEASE', build_release)
        srpm_path = config.get(args.config_section, 'srpm_path').replace('DIST', dist).replace('RELEASE', build_release)
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
        if rpms_released and update:
            update_repo(host, rpm_path, args.pkey, args.gpgpass)
        if srpms_released and update:
            update_repo(host, srpm_path, args.pkey, args.gpgpass)

if __name__ == '__main__':
    main()
