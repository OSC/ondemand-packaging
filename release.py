#!/usr/bin/env python

import argparse
try:
    import ConfigParser
except ModuleNotFoundError:
    import configparser as ConfigParser
import datetime
import logging
import os
import paramiko
import re
import subprocess
import sys
import tempfile


logger = logging.getLogger()

deb_dist_map = {
    'ubuntu-18.04': 'bionic',
    'ubuntu-20.04': 'focal',
    'ubuntu-22.04': 'jammy',
}
PROJ_ROOT = os.path.dirname(os.path.realpath(__file__))

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

def update_repo(host, release, dist, pkey):
    _pkey = paramiko.RSAKey.from_private_key_file(pkey)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username='oodpkg', password=None, pkey=_pkey)
    sftp = ssh.open_sftp()
    repo_update_src = os.path.join(PROJ_ROOT, 'repo-update.sh')
    repo_update_dest = '/var/lib/oodpkg/repo-update.sh'
    logger.info("SFTP %s -> oodpkg@%s:%s", repo_update_src, host, repo_update_dest)
    sftp.put(repo_update_src, repo_update_dest)
    repo_update_cmd = "/bin/bash %s -r %s -d %s" % (repo_update_dest, release, dist)
    logger.info("Executing via SSH oodpkg@%s '%s'", host, repo_update_cmd)
    stdin, stdout, stderr = ssh.exec_command(repo_update_cmd)
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
        %(prog)s /tmp/output/*

    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog=usage_examples)
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    parser.add_argument('-f', '--force', help='overwrite existing RPMs', action='store_true', default=False)
    parser.add_argument('--pkey', help='SSH private key to use for uploading RPMs (default: %(default)s)', default=pkey)
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
    release = config.get(args.config_section, 'release').replace('RELEASE', build_release)

    for release_dir in args.dirs:
        dist = os.path.basename(release_dir)
        deb = False
        if dist in deb_dist_map:
            deb = deb_dist_map[dist]
        if deb:
            deb_basepath = config.get(args.config_section, 'deb_path').replace('DIST', deb).replace('RELEASE', build_release)
            if args.config_section == 'release':
                pool_path = deb_basepath
            else:
                pool_path = os.path.join(deb_basepath, 'pool', deb)
            debs = []
            for f in os.listdir(release_dir):
                p = os.path.join(release_dir, f)
                if p.endswith('.deb'):
                    logger.debug("Found deb: %s", p)
                    debs.append(p)
            debs_released = release_packages(debs, host, pool_path, args.pkey, args.force)
            if debs_released and update:
                update_repo(host, release, deb, args.pkey)
        else:
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
                update_repo(host, release, dist, args.pkey)
            if srpms_released and update:
                update_repo(host, release, dist, args.pkey)

if __name__ == '__main__':
    main()
