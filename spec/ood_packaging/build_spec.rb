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
  let(:arch) { 'x86_64' }
  let(:version) { 'v0.0.1-2' }
  let(:build) { described_class.new }
  let(:cmd_suffix) { ' 2>/dev/null 1>/dev/null' }

  before do
    ENV['DIST'] = dist
    ENV['ARCH'] = arch
    ENV['VERSION'] = version
    ENV['GPG_NAME'] = 'GPG'
    FileUtils.mkdir_p(work_dir)
    FileUtils.mkdir_p(package_dir)
    allow(build).to receive(:dist).and_return('el8')
    allow(build).to receive(:package).and_return('ondemand')
    allow(build).to receive(:spec_file).and_return(spec_file)
    allow(build).to receive(:work_dir).and_return(work_dir)
  end

  after do
    ENV.delete('DIST')
    ENV.delete('VERSION')
    ENV.delete('GPG_NAME')
    FileUtils.remove_entry(tmp)
  end

  describe 'output_dir' do
    it 'uses arch' do
      expect(build.output_dir).to eq('/output/el8-x86_64')
    end

    context 'when aarch64' do
      let(:arch) { 'aarch64' }

      it 'uses aarch64 arch' do
        expect(build.output_dir).to eq('/output/el8-aarch64')
      end
    end
  end

  describe 'bootstrap_rpm!' do
    it 'bootstraps RPM build environment' do
      allow(build).to receive(:gpg_sign?).and_return(true)
      expect(build).to receive(:sh).with("sed -i 's|@GPG_NAME@|GPG|g' /home/ood/.rpmmacros")
      expected_gpg_cmd = [
        'gpg', '--batch', '--passphrase-file /ondemand-packaging/.gpgpass',
        '--import /ondemand-packaging/ondemand.sec', '2>/dev/null 1>/dev/null'
      ]
      expect(build).to receive(:sh).with(expected_gpg_cmd.join(' '))
      expect(build).to receive(:sh).with("mkdir -p #{work_dir}/{RPMS,SRPMS,SOURCES,SPECS,rpmbuild/BUILD}")
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
      expect(build).to receive(:sh).with("dch -b -v 0.0.1 --controlmaint 'Release 0.0.1' 2>/dev/null 1>/dev/null")
      build.bootstrap_deb!
    end

    context 'when ubuntu-22.04' do
      let(:dist) { 'ubuntu-22.04' }
      let(:version) { 'v0.0.1' }

      it 'bootstraps DEB build environment with release' do
        expect(build).to receive(:sh).with("cp -a /package/build/* #{work_dir}/")
        expect(build).to receive(:sh).with('tar -xf ondemand-0.0.1.tar.gz')
        expected_dh_make = [
          'dh_make -s -y --createorig',
          '-f ../ondemand-0.0.1.tar.gz',
          '2>/dev/null 1>/dev/null || true'
        ]
        expect(build).to receive(:sh).with(expected_dh_make.join(' '))
        expect(build).to receive(:sh).with("dch -b -v 0.0.1 --controlmaint 'Release 0.0.1' 2>/dev/null 1>/dev/null")
        build.bootstrap_deb!
      end
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
      let(:cleanup) do
        [
          'ondemand-build-deps*.buildinfo',
          'ondemand-build-deps*.changes'
        ]
      end
      let(:expected_cmd) do
        tool = [
          'DEBIAN_FRONTEND=noninteractive apt-cudf-get --solver aspcud',
          '-o APT::Get::Assume-Yes=1 -o APT::Get::Allow-Downgrades=1',
          '-o Debug::pkgProblemResolver=0 -o APT::Install-Recommends=0'
        ]
        [
          'mk-build-deps', '--install', '--remove', '--root-cmd sudo',
          "--tool='#{tool.join(' ')}'",
          '2>/dev/null 1>/dev/null'
        ]
      end

      it 'installs DEB dependencies using apt' do
        expect(build).to receive(:sh).with('sudo apt update -y 2>/dev/null 1>/dev/null')
        expect(build).to receive(:sh).with("sed -i 's|@EXTRA_DEPENDS@||g' debian/control#{cmd_suffix}")
        expect(build).to receive(:sh).with(expected_cmd.join(' '))
        expect(build).to receive(:sh).with("rm -f #{cleanup.join(' ')} 2>/dev/null 1>/dev/null")
        build.install_dependencies!
      end

      context 'when extra_depends is defined' do
        let(:dist) { 'debian-12' }

        it 'updates debian/control' do
          allow(build).to receive(:packaging_config).and_return(
            {
              'debian-12' => { 'extra_depends' => 'npm' }
            }
          )
          expect(build).to receive(:sh).with('sudo apt update -y 2>/dev/null 1>/dev/null')
          expect(build).to receive(:sh).with("sed -i 's|@EXTRA_DEPENDS@|, npm|g' debian/control#{cmd_suffix}")
          expect(build).to receive(:sh).with(expected_cmd.join(' '))
          expect(build).to receive(:sh).with("rm -f #{cleanup.join(' ')} 2>/dev/null 1>/dev/null")
          build.install_dependencies!
        end

        it 'updates debian/control from array of extra_depends' do
          allow(build).to receive(:packaging_config).and_return(
            {
              'debian-12' => { 'extra_depends' => ['npm', 'foo'] }
            }
          )
          depends = ', npm, foo'
          expect(build).to receive(:sh).with('sudo apt update -y 2>/dev/null 1>/dev/null')
          expect(build).to receive(:sh).with("sed -i 's|@EXTRA_DEPENDS@|#{depends}|g' debian/control#{cmd_suffix}")
          expect(build).to receive(:sh).with(expected_cmd.join(' '))
          expect(build).to receive(:sh).with("rm -f #{cleanup.join(' ')} 2>/dev/null 1>/dev/null")
          build.install_dependencies!
        end
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

    context 'when building for EL7' do
      let(:dist) { 'el7' }

      it 'executes rpmbuild with scl define' do
        allow(build).to receive(:packaging_config).and_return({ 'el7' => { 'scl' => 'httpd24' } })
        expected_cmd = [
          'rpmbuild', '-ba',
          '--define', "'git_tag v0.0.1-2'",
          '--define', "'package_version 0.0.1'",
          '--define', "'package_release 2'",
          '--define', "'scl httpd24'",
          spec_file, '2>/dev/null 1>/dev/null'
        ]
        expect(build).to receive(:sh).with(expected_cmd.join(' '))
        build.rpmbuild!
      end
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
