# frozen_string_literal: true

require 'spec_helper'
require 'tmpdir'

describe OodPackaging::Package do
  let(:tmp) { Dir.mktmpdir }
  let(:dist) { 'el8' }
  let(:arch) { 'x86_64' }
  let(:default_config) do
    {
      dist:       dist,
      arch:       arch,
      package:    File.join(tmp, 'package'),
      work_dir:   File.join(tmp, 'work'),
      output_dir: File.join(tmp, 'output'),
      version:    'v0.0.1'
    }
  end
  let(:config) { default_config }
  let(:package) { described_class.new(config) }

  before do
    FileUtils.mkdir_p(config[:package])
    allow(Process).to receive(:uid).and_return(1000)
    allow(Process).to receive(:gid).and_return(1000)
    allow(package.build_box).to receive(:dist).and_return(dist)
    allow(package.build_box).to receive(:build_dir).and_return('/fake-builddir')
    allow(package.build_box).to receive(:image_tag).and_return('image-tag')
    allow(package).to receive(:podman_runtime?).and_return(false)
    allow(package).to receive(:tar).and_return('tar')
    allow(package).to receive(:container_name).and_return('uuid')
    allow(package).to receive(:gpg_sign).and_return(false)
  end

  after do
    FileUtils.remove_entry(tmp)
  end

  describe 'package_name' do
    it 'works with root of project' do
      allow(package).to receive(:package).and_return('/dne/ondemand')
      expect(package.package_name).to eq('ondemand')
    end

    it 'works with packaging directory' do
      allow(package).to receive(:package).and_return('/dne/ondemand/packaging')
      expect(package.package_name).to eq('ondemand')
    end

    it 'works with direct path' do
      allow(package).to receive(:package).and_return('/dne/packages/ondemand/deb')
      expect(package.package_name).to eq('ondemand')
    end
  end

  describe 'gpg_name' do
    it 'uses legacy key' do
      expect(package.gpg_name).to eq('OnDemand Release Signing Key')
    end

    context 'when el9' do
      let(:dist) { 'el9' }

      it 'uses legacy key' do
        expect(package.gpg_name).to eq('OnDemand Release Signing Key (SHA512)')
      end
    end
  end

  describe 'tar!' do
    context 'when packaging for EL' do
      before do
        FileUtils.mkdir_p(config[:package])
      end

      it 'creates tar archive' do
        expected_cmd = [
          'git', 'ls-files', '.', '|', 'tar', '-c',
          "--transform 's,^,package-0.0.1/,'",
          '-h', '--hard-dereference', '-T', '-', '|',
          'gzip >', File.join(config[:package], 'packaging/rpm', 'package-0.0.1.tar.gz')
        ]
        expect(package).to receive(:sh).with(expected_cmd.join(' '), verbose: false)
        package.tar!
      end
    end

    context 'when packaging for DEB' do
      let(:dist) { 'ubuntu-24.04' }

      it 'creates tar archive' do
        expected_cmd = [
          'git', 'ls-files', '.', '|', 'tar', '-c',
          "--transform 'flags=r;s,packaging/deb,debian,'",
          "--transform 's,^,package-0.0.1/,'",
          '-h', '--hard-dereference', '-T', '-', '|',
          'gzip >', File.join(config[:package], 'build', 'package-0.0.1.tar.gz')
        ]
        FileUtils.mkdir_p(File.join(config[:package], 'build'))
        expect(package).to receive(:sh).with("mkdir -p #{File.join(config[:package], 'build')}")
        expect(package).to receive(:sh).with(expected_cmd.join(' '), verbose: false)
        package.tar!
      end

      it 'creates tar archive when using packages path' do
        allow(Dir).to receive(:exist?).with(File.join(config[:package], 'deb')).and_return(true)
        expected_cmd = [
          'git', 'ls-files', '.', '|', 'tar', '-c',
          "--transform 'flags=r;s,packaging/deb,debian,'",
          "--transform 's,^,package-0.0.1/,'",
          '-h', '--hard-dereference', '-T', '-', '|',
          'gzip >', File.join(config[:package], 'deb/build', 'package-0.0.1.tar.gz')
        ]
        FileUtils.mkdir_p(File.join(config[:package], 'deb', 'build'))
        expect(package).to receive(:sh).with("mkdir -p #{File.join(config[:package], 'deb', 'build')}")
        expect(package).to receive(:sh).with(expected_cmd.join(' '), verbose: false)
        package.tar!
      end
    end
  end

  describe 'run!' do
    it 'runs packaging' do
      allow(package).to receive(:container_running?).and_return(true)
      expect(package).to receive(:clean!)
      expect(package).to receive(:bootstrap!)
      expect(package).not_to receive(:tar!)
      expect(package).to receive(:container_start!)
      expect(package).to receive(:container_exec!)
      expect(package).to receive(:container_kill!)
      package.run!
    end

    it 'runs tar only' do
      config[:tar_only] = true
      expect(package).not_to receive(:clean!)
      expect(package).not_to receive(:bootstrap!)
      expect(package).to receive(:tar!)
      expect(package).not_to receive(:container_start!)
      expect(package).not_to receive(:container_exec!)
      expect(package).not_to receive(:container_kill!)
      package.run!
    end

    context 'when running for DEB' do
      let(:dist) { 'ubuntu-24.04' }

      it 'runs packaging' do
        allow(package).to receive(:container_running?).and_return(true)
        expect(package).to receive(:clean!)
        expect(package).to receive(:bootstrap!)
        expect(package).to receive(:tar!)
        expect(package).to receive(:container_start!)
        expect(package).to receive(:container_exec!)
        expect(package).to receive(:container_kill!)
        package.run!
      end
    end
  end

  describe 'container_start!' do
    it 'runs container' do
      expected_command = [
        'docker', 'run', '--detach', '--rm', '--platform linux/amd64',
        '--name', 'uuid', '--privileged', '--tty',
        '-v', "#{config[:package]}:/package:ro",
        '-v', "#{config[:work_dir]}:/work", '-v', "#{config[:output_dir]}:/output",
        'image-tag', '/sbin/init', '1>/dev/null'
      ]
      expect(package).to receive(:sh).with(expected_command.join(' '), verbose: false)
      package.container_start!
    end

    context 'when arch is aarch64' do
      let(:arch) { 'aarch64' }

      it 'runs container' do
        expected_command = [
          'docker', 'run', '--detach', '--rm', '--platform linux/arm64',
          '--name', 'uuid', '--privileged', '--tty',
          '-v', "#{config[:package]}:/package:ro",
          '-v', "#{config[:work_dir]}:/work", '-v', "#{config[:output_dir]}:/output",
          'image-tag', '/sbin/init', '1>/dev/null'
        ]
        expect(package).to receive(:sh).with(expected_command.join(' '), verbose: false)
        package.container_start!
      end
    end
  end

  describe 'container_exec!' do
    it 'execs container with Rake' do
      expected_command = [
        'docker', 'exec',
        '-e', "'DIST=el8'", '-e', "'ARCH=x86_64'", '-e', "'PACKAGE=package'", '-e', "'VERSION=v0.0.1'", '-e',
        "'TAR_NAME=package-0.0.1.tar.gz'",
        '-e', "'GPG_SIGN=false'", '-e', "'GPG_NAME=OnDemand Release Signing Key'",
        '-e', "'OOD_UID=1000'", '-e', "'OOD_GID=1000'",
        '-e', "'DEBUG=false'",
        'uuid', '/ondemand-packaging/inituidgid.sh', '/ondemand-packaging/setuser.rb', 'ood',
        '/ondemand-packaging/rake', '-q', '-f', '/ondemand-packaging/Rakefile', 'ood_packaging:package:build'
      ]
      expect(package).to receive(:sh).with(expected_command.join(' '), verbose: false)
      package.container_exec!(package.exec_rake)
    end

    context 'when aarch64' do
      let(:arch) { 'aarch64' }

      it 'execs container with Rake using aarch64' do
        expected_command = [
          'docker', 'exec',
          '-e', "'DIST=el8'", '-e', "'ARCH=aarch64'", '-e', "'PACKAGE=package'", '-e', "'VERSION=v0.0.1'", '-e',
          "'TAR_NAME=package-0.0.1.tar.gz'",
          '-e', "'GPG_SIGN=false'", '-e', "'GPG_NAME=OnDemand Release Signing Key'",
          '-e', "'OOD_UID=1000'", '-e', "'OOD_GID=1000'",
          '-e', "'DEBUG=false'",
          'uuid', '/ondemand-packaging/inituidgid.sh', '/ondemand-packaging/setuser.rb', 'ood',
          '/ondemand-packaging/rake', '-q', '-f', '/ondemand-packaging/Rakefile', 'ood_packaging:package:build'
        ]
        expect(package).to receive(:sh).with(expected_command.join(' '), verbose: false)
        package.container_exec!(package.exec_rake)
      end
    end
  end
end
