# frozen_string_literal: true

require 'spec_helper'
require 'tmpdir'

describe OodPackaging::Build do
  let(:tmp) { Dir.mktmpdir }
  let(:spec_dir) { File.join(tmp, 'SPEC') }
  let(:spec_file) { File.join(tmp, 'package.spec') }
  let(:work_dir) { File.join(tmp, 'work') }
  let(:package_dir) { File.join(work_dir, 'ondemand-0.0.1') }
  let(:dist) { 'el8' }
  let(:version) { 'v0.0.1-2' }
  let(:build) { described_class.new }

  before do
    ENV['DIST'] = dist
    ENV['VERSION'] = version
    ENV['GPG_NAME'] = 'GPG'
    FileUtils.mkdir_p(work_dir)
    FileUtils.mkdir_p(package_dir)
    allow(build).to receive(:dist).and_return('el8')
    allow(build).to receive(:package_name).and_return('ondemand')
    allow(build).to receive(:spec_file).and_return(spec_file)
    allow(build).to receive(:work_dir).and_return(work_dir)
  end

  after do
    ENV.delete('DIST')
    ENV.delete('VERSION')
    ENV.delete('GPG_NAME')
    FileUtils.remove_entry(tmp)
  end

  describe 'package_name' do
    it 'works with root of project' do
      allow(build).to receive(:package).and_return('/dne/ondemand')
      expect(build.package_name).to eq('ondemand')
    end

    it 'works with direct path' do
      allow(build).to receive(:package).and_return('/dne/packages/ondemand/deb')
      expect(build.package_name).to eq('ondemand')
    end
  end

  describe 'bootstrap_rpm!' do
    it 'bootstraps RPM build environment' do
      allow(build).to receive(:gpg_sign?).and_return(true)
      expect(build).to receive(:sh).with("rm -rf #{work_dir}/*")
      expect(build).to receive(:sh).with("sed -i 's|@GPG_NAME@|GPG|g' /home/ood/.rpmmacros")
      expected_gpg_cmd = [
        'gpg', '--batch', '--passphrase-file /ondemand-packaging/.gpgpass',
        '--import /ondemand-packaging/ondemand.sec', '2>/dev/null 1>/dev/null'
      ]
      expect(build).to receive(:sh).with(expected_gpg_cmd.join(' '))
      expect(build).to receive(:sh).with('rpmdev-setuptree 2>/dev/null 1>/dev/null')
      expect(build).to receive(:sh).with("find /package -maxdepth 1 -type f -exec cp {} #{work_dir}/SOURCES/ \\;")
      expected_find_d = [
        'find /package', '-maxdepth 1 -mindepth 1 -type d',
        "-exec cp -r {} #{work_dir}/SOURCES/ \\;"
      ]
      expect(build).to receive(:sh).with(expected_find_d.join(' '))
      expected_spectool_cmd = [
        'spectool',
        "--define 'git_tag v0.0.1-2'",
        "--define 'package_version 0.0.1'",
        "--define 'package_release 2'",
        '-g -R -S', spec_file, '2>/dev/null 1>/dev/null'
      ]
      expect(build).to receive(:sh).with(expected_spectool_cmd.join(' '))
      build.bootstrap_rpm!
    end
  end

  describe 'bootstrap_deb!' do
    let(:dist) { 'ubuntu-20.04' }
    let(:version) { 'v0.0.1' }

    it 'bootstraps DEB build environment' do
      expect(build).to receive(:sh).with("cp -a /package/build/* #{work_dir}/")
      expect(build).to receive(:sh).with('tar -xf ondemand-0.0.1.tar.gz')
      expected_dh_make = [
        'dh_make -s -y --createorig',
        '-f ../ondemand-0.0.1.tar.gz',
        '2>/dev/null 1>/dev/null || true'
      ]
      expect(build).to receive(:sh).with(expected_dh_make.join(' '))
      expect(build).to receive(:sh).with("dch -b -v 0.0.1 'Release 0.0.1' 2>/dev/null 1>/dev/null")
      build.bootstrap_deb!
    end
  end

  describe 'install_dependencies!' do
    context 'when installing on EL8' do
      it 'installs RPM dependencies using DNF' do
        expected_cmd = [
          'sudo', 'dnf', 'builddep', '-y',
          "--define 'git_tag v0.0.1-2'",
          "--define 'package_version 0.0.1'",
          "--define 'package_release 2'",
          '--spec', spec_file, '2>/dev/null 1>/dev/null'
        ]
        expect(build).to receive(:sh).with(expected_cmd.join(' '))
        build.install_dependencies!
      end
    end

    context 'when installing on EL7' do
      let(:dist) { 'el7' }

      it 'installs RPM dependencies using YUM' do
        expected_cmd = [
          'sudo', 'yum-builddep', '-y',
          "--define 'git_tag v0.0.1-2'",
          "--define 'package_version 0.0.1'",
          "--define 'package_release 2'",
          spec_file, '2>/dev/null 1>/dev/null'
        ]
        expect(build).to receive(:sh).with(expected_cmd.join(' '))
        build.install_dependencies!
      end
    end

    context 'when doing deb builds' do
      let(:dist) { 'ubuntu-20.04' }
      let(:version) { 'v0.0.1' }

      it 'installs DEB dependencies using apt' do
        expected_cmd = [
          'mk-build-deps', '--install', '--remove', '--root-cmd sudo',
          "--tool='apt-get -o Debug::pkgProblemResolver=yes --no-install-recommends --yes'",
          '2>/dev/null 1>/dev/null'
        ]
        expect(build).to receive(:sh).with(expected_cmd.join(' '))
        build.install_dependencies!
      end
    end
  end

  describe 'rpmbuild!' do
    it 'executes rpmbuild command' do
      expected_cmd = [
        'rpmbuild', '-ba',
        '--define', "'git_tag v0.0.1-2'",
        '--define', "'package_version 0.0.1'",
        '--define', "'package_release 2'",
        spec_file, '2>/dev/null 1>/dev/null'
      ]
      expect(build).to receive(:sh).with(expected_cmd.join(' '))
      build.rpmbuild!
    end
  end

  describe 'debuild!' do
    let(:version) { 'v0.0.1' }

    it 'executes debuild command' do
      expected_cmd = ['debuild', '--no-lintian', '--preserve-env', ' 2>/dev/null 1>/dev/null']
      expect(build).to receive(:sh).with(expected_cmd.join(' '))
      build.debuild!
    end
  end

  describe 'gpg_sign!' do
    before do
      allow(build).to receive(:rpms).and_return(['/output/ondemand.rpm', '/output/ondemand-selinux.rpm'])
    end

    it 'signs RPMs' do
      expect(build).to receive(:sh).with('rpmsign --addsign /output/ondemand.rpm 2>/dev/null 1>/dev/null')
      expect(build).to receive(:sh).with('rpmsign --addsign /output/ondemand-selinux.rpm 2>/dev/null 1>/dev/null')
      build.gpg_sign!
    end

    context 'when building for EL7' do
      let(:dist) { 'el7' }

      it 'signs RPMs' do
        expect(build).to receive(:sh).with(
          'cat /dev/null | setsid rpmsign --addsign /output/ondemand.rpm 2>/dev/null 1>/dev/null'
        )
        expect(build).to receive(:sh).with(
          'cat /dev/null | setsid rpmsign --addsign /output/ondemand-selinux.rpm 2>/dev/null 1>/dev/null'
        )
        build.gpg_sign!
      end
    end
  end
end
