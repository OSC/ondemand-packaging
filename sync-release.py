#!/usr/bin/env python

import argparse
import datetime
import getpass
import logging
import os
from pydpkg import Dpkg
import rpm
import shutil
import subprocess
import sys
import yaml

logger = logging.getLogger()


def get_rpm_info(rpm_file):
    ts = rpm.ts()
    fdno = os.open(rpm_file, os.O_RDONLY)
    try:
        hdr = ts.hdrFromFdno(fdno)
    except rpm.error:
        ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)
        hdr = ts.hdrFromFdno(fdno)
    os.close(fdno)
    info = {
        'name': hdr[rpm.RPMTAG_NAME],
        'ver': "%s-%s" % (hdr[rpm.RPMTAG_VERSION],hdr[rpm.RPMTAG_RELEASE])
    }
    return info

def get_deb_info(deb_file):
    dp = Dpkg(deb_file)
    info = dp.headers
    return info

def main():
    gpgpass = '/systems/osc_certs/gpg/ondemand/.gpgpass'
    usage_examples = """
Usage examples:

    Sync given release
        %(prog)s --release 1.3

    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog=usage_examples)
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    parser.add_argument('-f', '--force', help='overwrite existing RPMs', action='store_true', default=False)
    parser.add_argument('-c', '--clean', help='remove non-manifest RPMs from release repo', action='store_true', default=False)
    parser.add_argument('-b', '--repo-base', help="Repo base directory (default: %(default)s)", default='/var/www/repos/public/ondemand')
    parser.add_argument('-m', '--manifest', help="Release manifest path (default: %(default)s)", default=os.path.join(os.path.dirname(__file__), 'release-manifest.yaml'))
    parser.add_argument('-r', '--release', help="Release version", required=True)
    parser.add_argument('-g','--gpgpass', help='GPG passphrase file (default: %(default)s)', default=gpgpass)
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

    user = getpass.getuser()
    if user != 'oodpkg':
        logger.error("Only run this script as oodpkg, not %s", user)
        sys.exit(1)

    latest_dir = os.path.join(args.repo_base, 'latest')
    release_dir = os.path.join(args.repo_base, args.release)
    rpms = []
    debs = []
    manifest = {}
    manifest_data = {}
    copied_manifest = {}

    # Read manifest
    if os.path.isfile(args.manifest):
        with open(args.manifest, 'r') as f:
            manifest_data = yaml.load(f)
    else:
        logger.error("Manifest %s not found", args.manifest)

    # Get global values
    major = manifest_data.get('major', args.release)
    full = manifest_data.get('full', None)
    if full is None:
        logger.error("Unable to determine full version of ondemand")
        sys.exit(1)

    # Build manifest
    for k,v in manifest_data.iteritems():
        if k in ['major','full']:
            continue
        name = k.format(major=major, full=full)
        if isinstance(v, dict):
            for p in v['packages']:
                name = p.format(major=major, full=full)
                manifest[name] = []
                for val in v['versions']:
                    value = val.format(major=major, full=full)
                    manifest[name].append(value)
        else:
            manifest[name] = []
            for val in v:
                value = val.format(major=major, full=full)
                manifest[name].append(value)

    # Print manifest
    logger.debug("MANIFEST:")
    for name, versions in sorted(manifest.items(), key=lambda item: item[0]):
        logger.debug("%s: %s", name, ','.join(versions))
    logger.debug("END MANIFEST:")
    #sys.exit(0)

    # Prep release directories
    for t in ['compute', 'web']:
        for rel in ['el7', 'el8']:
            rel_d = os.path.join(release_dir, t, rel)
            if not os.path.isdir(rel_d):
                logger.info("mkdir -p %s", rel_d)
                os.makedirs(rel_d, 0755)
            rel_l = "%sServer" % rel_d
            if not os.path.islink(rel_l):
                logger.info("ln -s %s %s", rel, rel_l)
                os.symlink(rel, rel_l)
            for arch in ['SRPMS', 'x86_64']:
                d = os.path.join(release_dir, t, rel, arch)
                if not os.path.isdir(d):
                    logger.info("mkdir -p %s", d)
                    os.makedirs(d, 0755)
        for rel in ['focal']:
            rel_d = os.path.join(release_dir, t, 'apt/dists', rel, 'main/binary-amd64')
            if not os.path.isdir(rel_d):
                logger.info("mkdir -p %s", rel_d)
                os.makedirs(rel_d, 0755)

    if args.release in ['latest','ci','nightly'] or args.release.startswith('build'):
        logger.info("Latest release does not require sync, exiting")
        sys.exit(0)

    # Get lists of all SRPMs and RPMs
    for root, dirnames, filenames in os.walk(latest_dir):
        for filename in filenames:
            f = os.path.join(root, filename)
            if f.endswith('.rpm'):
                rpms.append(f)
            elif f.endswith('.deb'):
                debs.append(f)


    # Determine if SRPM/RPM needs to be copie to release repo
    # If a given SRPM/RPM is in the manifest, copy to release repo
    for r in sorted(rpms):
        copy = True
        rpm_info = get_rpm_info(r)
        logger.debug("RPM info for %s: %s", r, rpm_info)
        name = rpm_info['name']
        if name not in manifest:
            logger.warning("%s not in manifest", name)
            continue
        version = rpm_info['ver'].replace('.el7', '').replace('.el8', '')
        if version not in manifest[name]:
            logger.debug("Skipping %s-%s, not in manifest", name, version)
            continue
        dest = r.replace('/latest/', "/%s/" % args.release)
        if os.path.isfile(dest) and not args.force:
            copy = False
            logger.debug("%s already exists, skipping", dest)
        if name in copied_manifest:
            if version not in copied_manifest[name]:
                copied_manifest[name].append(version)
        else:
            copied_manifest[name] = [version]
        if not copy:
            continue
        logger.info("Copy %s -> %s", r, dest)
        shutil.copy2(r, dest)

    for d in sorted(debs):
        copy = True
        deb_info = get_deb_info(d)
        logger.debug("DEB info for %s: %s", d, deb_info)
        name = deb_info['Package']
        version = deb_info['Version']
        if name not in manifest:
            logger.warning("%s not in manifest", name)
            continue
        if version not in manifest[name]:
            logger.debug("Skipping %s-%s, not in manifest", name, version)
            continue
        dest = r.replace('/latest/', "/%s/" % args.release)
        if os.path.isfile(dest) and not args.force:
            copy = False
            logger.debug("%s already exists, skipping", dest)
        if name in copied_manifest:
            if version not in copied_manifest[name]:
                copied_manifest[name].append(version)
        else:
            copied_manifest[name] = [version]
        if not copy:
            continue
        logger.info("Copy %s -> %s", d, dest)
        shutil.copy2(d, dest)

    # Check for files in manifest that were not found in latest repo
    for name, versions in sorted(manifest.items(), key=lambda item: item[0]):
        if name not in copied_manifest:
            logger.error("Manifest item %s not found", name)
            continue
        for version in versions:
            if version not in copied_manifest[name]:
                logger.error("Manifest item version %s-%s not found", name, version)

    # Look for files in release repo that are not in manifest
    for root, dirnames, filenames in os.walk(release_dir):
        for filename in filenames:
            f = os.path.join(root, filename)
            found = False
            if filename.endswith('.rpm'):
                found = True
                rpm_info = get_rpm_info(f)
                name = rpm_info['name']
                version = rpm_info['ver'].replace('.el7', '').replace('.el8', '')
            elif filename.endswith('.deb'):
                found = True
                deb_info = get_deb_info(f)
                name = deb_info['Package']
                version = deb_info['Version']
            if found and name not in manifest or version not in manifest.get(name, []):
                logger.error("Package %s-%s should not be in release repo", name, version)
                if args.clean:
                    logger.debug("rm %s", f)
                    os.remove(f)

    # Run createrepo_c on each repo directory
    for root, dirnames, filenames in os.walk(release_dir):
        if os.path.basename(root) in ['SRPMS', 'x86_64']:
            logger.info("createrepo_c %s", root)
            process = subprocess.Popen(['createrepo_c', root], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate()
            exit_code = process.returncode
            if exit_code != 0:
                logger.error("Error: %s", err)
            repomd = os.path.join(root, 'repodata', 'repomd.xml')
            cmd = ['gpg','--detach-sign','--passphrase-file',args.gpgpass,'--batch','--yes','--no-tty','--armor',repomd]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate()
            exit_code = process.returncode
            if exit_code != 0:
                logger.error("Error: %s", err)
        elif os.path.basename(os.path.dirname(root)) == 'dists':
            base_path = os.path.dirname(os.path.dirname(root))
            dist = os.path.basename(root)
            dpkg_scanpackages_cmd = "dpkg-scanpackages --arch amd64 pool/%s > dists/%s/main/binary-amd64/Packages" % (dist, dist)
            dpkg_gzip_packages_cmd = "cat dists/%s/main/binary-amd64/Packages | gzip -9 > dists/%s/main/binary-amd64/Packages.gz" % (dist, dist)
            logger.info("Updating repo Packages at %s", root)
            process = subprocess.Popen(dpkg_scanpackages_cmd, shell=True, cwd=base_path)
            out, err = process.communicate()
            if exit_code != 0:
                logger.error("Error: %s", err)
                continue
            process = subprocess.Popen(dpkg_gzip_packages_cmd, shell=True, cwd=base_path)
            out, err = process.communicate()
            if exit_code != 0:
                logger.error("Error: %s", err)
                continue
            md5sum_cmd = "md5sum main/binary-amd64/Packages*"
            sha1sum_cmd = "sha1sum main/binary-amd64/Packages*"
            sha256sum_cmd = "sha256sum main/binary-amd64/Packages*"
            wc_cmd = "wc -c main/binary-amd64/Packages*" % dist_path
            process = subprocess.Popen(md5sum_cmd, shell=True, cwd=root)
            out, err = process.communicate()
            if exit_code != 0:
                logger.error("Error: %s", err)
                continue
            process = subprocess.Popen(sha1sum_cmd, shell=True, cwd=root)
            out, err = process.communicate()
            if exit_code != 0:
                logger.error("Error: %s", err)
                continue
            process = subprocess.Popen(sha256sum_cmd, shell=True, cwd=root)
            out, err = process.communicate()
            if exit_code != 0:
                logger.error("Error: %s", err)
                continue
            process = subprocess.Popen(wc_cmd, shell=True, cwd=root)
            out, err = process.communicate()
            if exit_code != 0:
                logger.error("Error: %s", err)
                continue
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
""".format(dist=dist, release=args.release, date=date, md5sums="\n".join(md5sums), sha1sums="\n".join(sha1sums), sha256sums="\n".join(sha256sums))
            with open(os.path.join(root, 'Release'), 'w') as f:
                f.write(release)
            gpg_cmd = "cat Release | gpg --detach-sign --passphrase-file %s --batch --yes --no-tty --digest-algo SHA256 --cert-digest-algo SHA256 --armor > Release.gpg" % args.gpgpass
            gpg_clearsign_cmd = "cat Release | gpg --detach-sign --passphrase-file %s --batch --yes --no-tty --digest-algo SHA256 --cert-digest-algo SHA256 --armor --clearsign > InRelease" % args.gpgpass
            process = subprocess.Popen(gpg_cmd, shell=True, cwd=root)
            out, err = process.communicate()
            exit_code = process.returncode
            if exit_code != 0:
                logger.error("Error: %s", err)
                continue
            process = subprocess.Popen(gpg_clearsign_cmd, shell=True, cwd=root)
            out, err = process.communicate()
            exit_code = process.returncode
            if exit_code != 0:
                logger.error("Error: %s", err)
                continue

if __name__ == '__main__':
    main()
