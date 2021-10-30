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
    'ubuntu-20.04': 'focal',
}

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
    createrepo_cmd = "cd %s ; createrepo_c --update ." % path
    gpg_cmd = "cd %s ; gpg --detach-sign --passphrase-file %s --batch --yes --no-tty --armor repodata/repomd.xml" % (path, gpgpass)
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

def update_apt_repo(host, path, dist, release, pkey, gpgpass):
    dist_path = os.path.join(path, 'dists', dist)
    _pkey = paramiko.RSAKey.from_private_key_file(pkey)
    dpkg_scanpackages_cmd = "cd %s ; dpkg-scanpackages --arch amd64 pool/%s > dists/%s/main/binary-amd64/Packages" % (path, dist, dist)
    dpkg_gzip_packages_cmd = "cd %s ; cat dists/%s/main/binary-amd64/Packages | gzip -9 > dists/%s/main/binary-amd64/Packages.gz" % (path, dist, dist)
    logger.info("Updating repo Packages at %s:%s", host, path)
    logger.debug("Executing via SSH oodpkg@%s '%s'", host, dpkg_scanpackages_cmd)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username='oodpkg', password=None, pkey=_pkey)
    dpkg_scanpackages_stdin, dpkg_scanpackages_stdout, dpkg_scanpackages_stderr = ssh.exec_command(dpkg_scanpackages_cmd)
    dpkg_scanpackages_out = dpkg_scanpackages_stdout.read()
    dpkg_scanpackages_err = dpkg_scanpackages_stderr.read()
    logger.debug("SSH CMD STDOUT:\n%s", dpkg_scanpackages_out)
    logger.debug("SSH CMD STDERR:\n%s", dpkg_scanpackages_err)
    logger.debug("Executing via SSH oodpkg@%s '%s'", host, dpkg_gzip_packages_cmd)
    dpkg_gzip_packages_stdin, dpkg_gzip_packages_stdout, dpkg_gzip_packages_stderr = ssh.exec_command(dpkg_gzip_packages_cmd)
    dpkg_gzip_packages_out = dpkg_gzip_packages_stdout.read()
    dpkg_gzip_packages_err = dpkg_gzip_packages_stderr.read()
    logger.debug("SSH CMD STDOUT:\n%s", dpkg_gzip_packages_out)
    logger.debug("SSH CMD STDERR:\n%s", dpkg_gzip_packages_err)
    md5sum_cmd = "cd %s ; md5sum main/binary-amd64/Packages*" % dist_path
    logger.debug("Executing via SSH oodpkg@%s '%s'", host, md5sum_cmd)
    md5sum_stdin, md5sum_stdout, md5sum_stderr = ssh.exec_command(md5sum_cmd)
    md5sum_out = md5sum_stdout.read().decode('ascii')
    md5sum_err = md5sum_stderr.read().decode('ascii')
    logger.debug("SSH CMD STDOUT:\n%s", md5sum_out)
    logger.debug("SSH CMD STDERR:\n%s", md5sum_err)
    sha1sum_cmd = "cd %s ; sha1sum main/binary-amd64/Packages*" % dist_path
    logger.debug("Executing via SSH oodpkg@%s '%s'", host, sha1sum_cmd)
    sha1sum_stdin, sha1sum_stdout, sha1sum_stderr = ssh.exec_command(sha1sum_cmd)
    sha1sum_out = sha1sum_stdout.read().decode('ascii')
    sha1sum_err = sha1sum_stderr.read().decode('ascii')
    logger.debug("SSH CMD STDOUT:\n%s", sha1sum_out)
    logger.debug("SSH CMD STDERR:\n%s", sha1sum_err)
    sha256sum_cmd = "cd %s ; sha256sum main/binary-amd64/Packages*" % dist_path
    logger.debug("Executing via SSH oodpkg@%s '%s'", host, sha256sum_cmd)
    sha256sum_stdin, sha256sum_stdout, sha256sum_stderr = ssh.exec_command(sha256sum_cmd)
    sha256sum_out = sha256sum_stdout.read().decode('ascii')
    sha256sum_err = sha256sum_stderr.read().decode('ascii')
    logger.debug("SSH CMD STDOUT:\n%s", sha256sum_out)
    logger.debug("SSH CMD STDERR:\n%s", sha256sum_err)
    wc_cmd = "cd %s ; wc -c main/binary-amd64/Packages*" % dist_path
    logger.debug("Executing via SSH oodpkg@%s '%s'", host, wc_cmd)
    wc_stdin, wc_stdout, wc_stderr = ssh.exec_command(wc_cmd)
    wc_out = wc_stdout.read().decode('ascii')
    wc_err = wc_stderr.read().decode('ascii')
    logger.debug("SSH CMD STDOUT:\n%s", wc_out)
    logger.debug("SSH CMD STDERR:\n%s", wc_err)
    utcnow = datetime.datetime.utcnow()
    date = utcnow.strftime("%a, %d %b %Y %H:%M:%S +0000")
    sizes = {}
    for line in wc_out.splitlines():
        items = line.strip().split(' ')
        if len(items) != 2:
            continue
        sizes[items[1]] = items[0]
    md5sums = []
    sha1sums = []
    sha256sums = []
    for line in md5sum_out.splitlines():
        items = line.strip().split()
        if len(items) != 2:
            continue
        if items[1] not in sizes:
            continue
        md5sums.append(" %s %s %s" % (items[0], sizes[items[1]], items[1]))
    for line in sha1sum_out.splitlines():
        items = line.strip().split()
        if len(items) != 2:
            continue
        if items[1] not in sizes:
            continue
        sha1sums.append(" %s %s %s" % (items[0], sizes[items[1]], items[1]))
    for line in sha256sum_out.splitlines():
        items = line.strip().split()
        if len(items) != 2:
            continue
        if items[1] not in sizes:
            continue
        sha256sums.append(" %s %s %s" % (items[0], sizes[items[1]], items[1]))
    release = """
Origin: OnDemand Repository
Label: OnDemand
Suite: stable
Codename: {dist}
Version: {release}
Architectures: amd64
Components: main
Description: OnDemand repository
Date: {date}
MD5Sum:
{md5sums}
SHA1:
{sha1sums}
SHA256:
{sha256sums}
""".format(dist=dist, release=release, date=date, md5sums="\n".join(md5sums), sha1sums="\n".join(sha1sums), sha256sums="\n".join(sha256sums))
    release_path = os.path.join(dist_path, 'Release')
    release_tmp = tempfile.NamedTemporaryFile(delete=False, mode='w')
    release_tmp.write(release)
    release_tmp.close()
    sftp = ssh.open_sftp()
    logger.debug("SFTP %s -> oodpkg@%s:%s", release_tmp.name, host, release_path)
    logger.info("Create Release at %s", release_path)
    sftp.put(release_tmp.name, release_path)
    gpg_cmd = "cd %s ; cat Release | gpg --detach-sign --passphrase-file %s --batch --yes --no-tty --digest-algo SHA256 --cert-digest-algo SHA256 --armor > Release.gpg" % (dist_path, gpgpass)
    logger.debug("Executing via SSH oodpkg@%s '%s'", host, gpg_cmd)
    gpg_stdin, gpg_stdout, gpg_stderr = ssh.exec_command(gpg_cmd)
    gpg_out = gpg_stdout.read()
    gpg_err = gpg_stderr.read()
    logger.debug("SSH CMD STDOUT:\n%s", gpg_out)
    logger.debug("SSH CMD STDERR:\n%s", gpg_err)
    gpg_clearsign_cmd = "cd %s ; cat Release | gpg --detach-sign --passphrase-file %s --batch --yes --no-tty --armor --digest-algo SHA256 --cert-digest-algo SHA256 --clearsign > InRelease" % (dist_path, gpgpass)
    logger.debug("Executing via SSH oodpkg@%s '%s'", host, gpg_clearsign_cmd)
    gpg_clearsign_stdin, gpg_clearsign_stdout, gpg_clearsign_stderr = ssh.exec_command(gpg_clearsign_cmd)
    gpg_clearsign_out = gpg_clearsign_stdout.read()
    gpg_clearsign_err = gpg_clearsign_stderr.read()
    logger.debug("SSH CMD STDOUT:\n%s", gpg_clearsign_out)
    logger.debug("SSH CMD STDERR:\n%s", gpg_clearsign_err)
    ssh.close()
    os.unlink(release_tmp.name)

def main():
    pkey = os.path.expanduser('~/.ssh/id_rsa')
    gpgpass = '/systems/osc_certs/gpg/ondemand/.gpgpass'
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
                update_apt_repo(host, deb_basepath, deb, args.config_section, args.pkey, args.gpgpass)
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
                update_repo(host, rpm_path, args.pkey, args.gpgpass)
            if srpms_released and update:
                update_repo(host, srpm_path, args.pkey, args.gpgpass)

if __name__ == '__main__':
    main()
