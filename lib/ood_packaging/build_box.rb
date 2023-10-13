# frozen_string_literal: true

require 'ood_packaging/utils'
require 'rake'
require 'rake/file_utils'

# Build the packaging build boxes
class OodPackaging::BuildBox
  include OodPackaging::Utils
  include FileUtils

  BASE_IMAGES = {
    'el7'          => 'centos:7',
    'el8'          => 'almalinux:8',
    'el9'          => 'almalinux:9',
    'ubuntu-20.04' => 'ubuntu:20.04',
    'ubuntu-22.04' => 'ubuntu:22.04',
    'debian-12'    => 'debian:12',
    'amzn2023'     => 'amazonlinux:2023'
  }.freeze

  CODENAMES = {
    'ubuntu-20.04' => 'focal',
    'ubuntu-22.04' => 'jammy',
    'debian-12'    => 'bookworm'
  }.freeze

  ARCH_PLATFORMS = {
    'x86_64'  => 'linux/amd64',
    'aarch64' => 'linux/arm64',
    'ppc64le' => 'linux/ppc64le'
  }.freeze

  def initialize(config = {})
    @config = config
    raise ArgumentError, 'Must provide dist' if dist.nil?

    # rubocop:disable Style/GuardClause
    unless valid_dist?(dist)
      raise ArgumentError, "Invalid dist selected: #{dist}. Valid choices are #{valid_dists.join(' ')}"
    end
    unless valid_arch?(arch)
      raise ArgumentError, "Invalid arch selected: #{arch}. Valid choices are #{valid_arches.join(' ')}"
    end
    # rubocop:enable Style/GuardClause
  end

  def dist
    @dist ||= ENV['OOD_PACKAGING_DIST'] || @config[:dist]
  end

  def arch
    @arch ||= ENV['OOD_PACKAGING_ARCH'] || @config[:arch] || 'x86_64'
  end

  def rpm?
    dist.start_with?('el') || dist.start_with?('amzn')
  end

  def deb?
    !rpm?
  end

  def dnf?
    return false unless rpm?
    return false if dist == 'el7'

    true
  end

  def scl?
    return true if dist == 'el7'

    false
  end

  def legacy_gpg?
    return true if ['el7', 'el8'].include?(dist)

    false
  end

  def package_manager
    return 'apt' if deb?
    return 'dnf' if dnf?

    'yum'
  end

  def valid_dist?(value)
    BASE_IMAGES.key?(value)
  end

  def valid_dists
    BASE_IMAGES.keys
  end

  def valid_arch?(value)
    ARCH_PLATFORMS.key?(value)
  end

  def valid_arches
    ARCH_PLATFORMS.keys
  end

  def base_image
    @base_image ||= BASE_IMAGES[dist]
  end

  def codename
    @codename ||= CODENAMES[dist]
  end

  def platform
    @platform ||= ARCH_PLATFORMS[arch]
  end

  def build_dir
    File.join(File.dirname(__FILE__), 'build_box/docker-image')
  end

  def work_dir
    File.join('/work', "#{dist}-#{arch}")
  end

  def image_registry
    @config[:build_box_registry] || ENV['OOD_PACKAGING_BUILD_BOX_REGISTRY'] || nil
  end

  def image_org
    @config[:build_box_org] || ENV['OOD_PACKAGING_BUILX_BOX_ORG'] || 'ohiosupercomputer'
  end

  def image_name
    @config[:build_box_name] || ENV['OOD_PACKAGING_BUILD_BOX_NAME'] || 'ood-buildbox'
  end

  def image_version
    (ENV['OOD_PACKAGING_BUILD_BOX_VERSION'] || OodPackaging::VERSION).gsub(/^v/, '')
  end

  def image_tag
    [image_registry, image_org, "#{image_name}-#{dist}-#{arch}:#{image_version}"].compact.join('/')
  end

  def build_gem
    gem = File.join(proj_root, 'pkg', "ood_packaging-#{OodPackaging::VERSION}.gem")
    Rake::Task['build'].invoke
    sh "rm -f #{build_dir}/*.gem"
    sh "cp #{gem} #{build_dir}/"
  end

  def dockerfile
    template_file('build_box/docker-image/Dockerfile.erb')
  end

  def scripts
    template_file('build_box/docker-image/inituidgid.sh.erb')
    template_file('build_box/docker-image/install.sh.erb')
  end

  def build_command
    if container_runtime == 'docker'
      ['buildx', 'build']
    else
      ['build']
    end
  end

  def build_output
    if container_runtime == 'docker'
      ['--output', 'type=docker']
    else
      []
    end
  end

  def build!
    scripts
    cmd = [container_runtime]
    cmd.concat build_command
    cmd.concat ['--platform', platform]
    cmd.concat ['--tag', image_tag]
    cmd.concat build_output
    cmd.concat [ENV['OOD_PACKAGING_BUILD_BOX_ARGS']] if ENV['OOD_PACKAGING_BUILD_BOX_ARGS']
    cmd.concat ['-f', dockerfile]
    cmd.concat [build_dir]
    build_gem
    sh cmd.join(' ')
  end

  def push!
    sh [container_runtime, 'push', image_tag].join(' ')
  end

  def pull!
    sh [container_runtime, 'pull', image_tag].join(' ')
  end

  def save!(path)
    sh [container_runtime, 'save', image_tag, '| gzip >', path].join(' ')
  end
end
