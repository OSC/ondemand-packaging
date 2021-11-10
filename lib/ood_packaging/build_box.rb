# frozen_string_literal: true

require 'ood_packaging/utils'
require 'rake'
require 'rake/file_utils'

# Build the packaging build boxes
class OodPackaging::BuildBox
  include OodPackaging::Utils
  include FileUtils

  def initialize(config = {})
    @config = config
    raise ArgumentError, 'Must provide dist' if @config[:dist].nil?
    raise ArgumentError, "Invalid dist selected: #{dist}" if base_image.nil?
  end

  def dist
    @dist ||= @config[:dist]
  end

  def rpm?
    dist.start_with?('el')
  end

  def deb?
    !rpm?
  end

  def dnf?
    return false unless rpm?
    return false if dist == 'el7'

    true
  end

  def package_manager
    return 'apt' if deb?
    return 'dnf' if dnf?

    'yum'
  end

  def ondemand_repo_url
    return 'https://yum.osc.edu/ondemand/latest/ondemand-release-web-latest-1-6.noarch.rpm' if rpm?
    return 'https://yum.osc.edu/ondemand/latest/ondemand-release-web-latest_1_all.deb' if deb?
  end

  def ondemand_build_repo
    '/build/2.1/'
  end

  def base_image
    @base_image ||= {
      'el7'          => 'centos:7',
      'el8'          => 'rockylinux/rockylinux:8',
      'ubuntu-20.04' => 'ubuntu:20.04'
    }[dist]
  end

  def build_dir
    File.join(File.dirname(__FILE__), 'build_box/docker-image')
  end

  def image_registry
    @config[:builx_box_registry] || ENV['OOD_PACKAGING_BUILD_BOX_REGISTRY'] || nil
  end

  def image_org
    @config[:build_box_org] || ENV['OOD_PACKAGING_BUILX_BOX_ORG'] || 'ohiosupercomputer'
  end

  def image_name
    @config[:builx_box_name] || ENV['OOD_PACKAGING_BUILD_BOX_NAME'] || 'ood-buildbox'
  end

  def image_tag
    [image_registry, image_org, "#{image_name}-#{dist}:#{OodPackaging::VERSION}"].compact.join('/')
  end

  def build_gem
    gem = File.join(proj_root, 'pkg', "ood_packaging-#{OodPackaging::VERSION}.gem")
    Rake::Task['build'].invoke
    sh "rm -f #{build_dir}/*.gem"
    sh "cp #{gem} #{build_dir}/"
  end

  def dockerfile
    file = template_file('build_box/docker-image/Dockerfile.erb')
    puts "DEBUG dockerfile=#{file}"
    file
  end

  def scripts
    template_file('build_box/docker-image/inituidgid.sh.erb')
    template_file('build_box/docker-image/install.sh.erb')
  end

  def build!
    scripts
    cmd = [container_runtime, 'build']
    cmd.concat ['--tag', image_tag]
    cmd.concat [ENV['OOD_PACKAGING_BUILD_BOX_ARGS']] if ENV['OOD_PACKAGING_BUILD_BOX_ARGS']
    cmd.concat ['-f', dockerfile]
    cmd.concat [build_dir]
    build_gem
    sh cmd.join(' ')
  end

  def push!
    sh [container_runtime, 'push', image_tag].join(' ')
  end
end
