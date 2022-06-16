# frozen_string_literal: true

require 'ood_packaging/build_box'
require 'ood_packaging/utils'
require 'ood_packaging/string_ext'
require 'English'
require 'pathname'
require 'ostruct'
require 'securerandom'
require 'rake'
require 'rake/file_utils'

# The interface to build packages using containers
class OodPackaging::Package
  include OodPackaging::Utils
  include FileUtils

  attr_accessor :build_box

  def initialize(config = {})
    @config = config
    @config[:dist] = 'el8' if tar_only?
    @build_box = OodPackaging::BuildBox.new(config)
    raise ArgumentError, 'Package is required' if package.nil?
    raise ArgumentError, 'Version is required' if version.nil?
    raise ArgumentError, "Package #{package} is not a directory" unless Dir.exist?(package)
    raise ArgumentError, "Package #{package} is not an absolute path" unless (Pathname.new package).absolute?
  end

  def container_name
    @container_name ||= SecureRandom.uuid
  end

  def debug
    return true if ENV['OOD_PACKAGING_DEBUG'] == 'true'

    @config[:debug].nil? ? false : @config[:debug]
  end

  def attach?
    return true if ENV['OOD_PACKAGING_ATTACH'] == 'true'

    @config[:attach].nil? ? false : @config[:attach]
  end

  def work_dir
    @work_dir ||= File.expand_path(@config[:work_dir])
  end

  def clean_work_dir
    return false if ENV['OOD_PACKAGING_CLEAN_WORK_DIR'] == 'false'

    @config[:clean_work_dir].nil? ? true : @config[:clean_work_dir]
  end

  def output_dir
    @output_dir ||= File.expand_path(@config[:output_dir])
  end

  def clean_output_dir
    return false if ENV['OOD_PACKAGING_CLEAN_OUTPUT_DIR'] == 'false'

    @config[:clean_output_dir].nil? ? true : @config[:clean_output_dir]
  end

  def package
    @config[:package]
  end

  def version
    @config[:version]
  end

  def tar_version
    version.gsub(/^v/, '')
  end

  def tar?
    @config[:tar].nil? ? build_box.deb? : @config[:tar]
  end

  def tar_only?
    @config[:tar_only].nil? ? false : @config[:tar_only]
  end

  def package_name
    name = File.basename(package)
    case name
    when /deb|rpm/
      name = if File.basename(File.dirname(package)) == 'packages'
               File.basename(File.dirname(File.dirname(package)))
             else
               File.basename(File.dirname(package))
             end
    when 'packaging'
      name = File.basename(File.dirname(package))
    end
    name
  end

  # rubocop:disable Metrics/AbcSize
  def gpg_files
    [
      OpenStruct.new(private_key: File.join(proj_root, 'ondemand-sha512.sec'),
                     passphrase:  File.join(proj_root, '.gpgpass')),
      OpenStruct.new(private_key: File.join(package, 'ondemand-sha512.sec'),
                     passphrase:  File.join(package, '.gpgpass')),
      OpenStruct.new(private_key: File.join(proj_root, 'ondemand.sec'), passphrase: File.join(proj_root, '.gpgpass')),
      OpenStruct.new(private_key: File.join(package, 'ondemand.sec'), passphrase: File.join(package, '.gpgpass')),
      OpenStruct.new(private_key: @config[:gpg_private_key], passphrase: @config[:gpg_passphrase]),
      OpenStruct.new(private_key: ENV['OOD_PACKAGING_GPG_PRIVATE_KEY'],
                     passphrase:  ENV['OOD_PACKAGING_GPG_PASSPHRASE'])
    ].each do |gpg|
      next if gpg.private_key.nil? || gpg.passphrase.nil?
      return gpg if File.exist?(gpg.private_key) && File.exist?(gpg.passphrase)
    end
    nil
  end
  # rubocop:enable Metrics/AbcSize

  def gpg_sign
    return false if ENV['OOD_PACKAGING_GPG_SIGN'].to_s == 'false'
    return false if @config[:gpg_sign] == false

    !gpg_files.nil?
  end

  def gpg_name
    @config[:gpg_name].nil? ? 'OnDemand Release Signing Key (SHA512)' : @config[:gpg_name]
  end

  def container_init
    '/sbin/init'
  end

  def tar_path
    if build_box.deb?
      path = File.join(package, 'deb')
      return path if Dir.exist?(path)
    end

    package
  end

  def tar_name
    version = if build_box.rpm?
                rpm_version
              else
                deb_version
              end
    "#{package_name}-#{version}"
  end

  def rpm_tar_dest_dir
    [
      File.join(package, 'rpm'),
      File.join(package, 'packaging/rpm'),
      File.join(package, 'packaging')
    ].each do |dir|
      return dir if Dir.exist?(dir)
    end
    File.join(package, 'packaging/rpm')
  end

  def rpm_version
    tar_version
  end

  def deb_tar_dest_dir
    dir = File.join(package, 'deb')
    return File.join(dir, 'build') if Dir.exist?(dir)

    File.join(package, 'build')
  end

  def deb_version
    tar_version.gsub('-', '.')
  end

  def exec_launchers
    [
      File.join(ctr_scripts_dir, 'inituidgid.sh'),
      File.join(ctr_scripts_dir, 'setuser.rb'),
      ctr_user
    ]
  end

  def exec_rake
    cmd = []
    cmd.concat exec_launchers if docker_runtime?
    cmd.concat ['scl', 'enable', scl_ruby, '--'] if podman_runtime? && build_box.scl?
    cmd.concat [File.join(ctr_scripts_dir, 'rake')]
    cmd.concat ['-q'] unless debug
    cmd.concat ['-f', File.join(ctr_scripts_dir, 'Rakefile'), 'ood_packaging:package:build']
    cmd
  end

  def exec_attach
    cmd = []
    cmd.concat exec_launchers if docker_runtime?
    cmd.concat ['/bin/bash']
    cmd
  end

  def container_mounts
    args = []
    args.concat ['-v', "#{package}:/package:ro"]
    args.concat ['-v', "#{@config[:gpg_pubkey]}:/gpg.pub:ro"] if @config[:gpg_pubkey]
    args.concat ['-v', "#{work_dir}:/work"]
    args.concat ['-v', "#{output_dir}:/output"]
    if gpg_sign
      args.concat ['-v', "#{gpg_files.private_key}:#{gpg_private_key}:ro"]
      args.concat ['-v', "#{gpg_files.passphrase}:#{gpg_passphrase}:ro"]
    end
    args
  end

  def clean!
    sh "rm -rf #{work_dir}", verbose: debug if clean_work_dir
    sh "rm -rf #{output_dir}", verbose: debug if clean_output_dir
  end

  def bootstrap!
    sh "mkdir -p #{work_dir}", verbose: debug
    sh "mkdir -p #{output_dir}", verbose: debug
  end

  def tar!
    cmd = ['git', 'ls-files', '.', '|', tar, '-c']
    if build_box.rpm?
      dir = rpm_tar_dest_dir
    else
      dir = deb_tar_dest_dir.tap { |p| sh "mkdir -p #{p}" }
      cmd.concat ["--transform 'flags=r;s,packaging/deb,debian,'"]
    end
    tar_file = "#{dir}/#{tar_name}.tar.gz"
    cmd.concat ["--transform 's,^,#{tar_name}/,'"]
    cmd.concat ['-T', '-', '|', "gzip > #{tar_file}"]

    sh "rm #{tar_file}" if File.exist?(tar_file)
    puts "Create tar archive #{tar_file}".blue
    Dir.chdir(tar_path) do
      sh cmd.join(' '), verbose: debug
    end
  end

  def run!
    if tar_only?
      tar!
      return
    end
    clean!
    bootstrap!
    tar! if tar?
    container_start!
    container_exec!(exec_rake)
  rescue RuntimeError
    # ret = 1
    puts "Build FAILED package=#{package} dist=#{build_box.dist}".red
    raise
  else
    puts "Build SUCCESS: package=#{package} dist=#{build_box.dist}".green
  ensure
    container_exec!(exec_attach, ['-i', '-t']) if attach?
    container_kill! if container_running?
  end

  def container_running?
    `#{container_runtime} inspect #{container_name} 2>/dev/null 1>/dev/null`
    $CHILD_STATUS.success?
  end

  def container_start!
    cmd = [container_runtime, 'run', '--detach', '--rm']
    cmd.concat ['--name', container_name]
    cmd.concat rt_specific_flags
    cmd.concat container_mounts
    cmd.concat [build_box.image_tag]
    cmd.concat [container_init]
    cmd.concat ['1>/dev/null'] unless debug
    puts "Starting container #{container_name} using image #{build_box.image_tag}".blue
    sh cmd.join(' '), verbose: debug
  end

  def container_exec!(exec_cmd, extra_args = [])
    cmd = [container_runtime, 'exec']
    cmd.concat extra_args
    container_env.each_pair do |k, v|
      cmd.concat ['-e', "'#{k}=#{v}'"] unless v.nil?
    end
    cmd.concat [container_name]
    cmd.concat exec_cmd
    puts "Build STARTED: package=#{package} dist=#{build_box.dist} exec=#{exec_cmd[-1]}".blue
    sh cmd.join(' '), verbose: debug
  rescue RuntimeError
    container_kill! if container_running?
  end

  def container_kill!
    puts "Killing container #{container_name}".blue
    cmd = [container_runtime, 'kill', container_name]
    cmd.concat ['1>/dev/null', '2>/dev/null'] unless debug
    sh cmd.join(' '), verbose: debug
  end

  def container_env
    env = {
      'DIST'          => build_box.dist,
      'PACKAGE'       => package_name,
      'VERSION'       => version,
      'TAR_NAME'      => "#{tar_name}.tar.gz",
      'GPG_SIGN'      => gpg_sign,
      'GPG_NAME'      => gpg_name,
      'SKIP_DOWNLOAD' => @config[:skip_download],
      'OOD_UID'       => Process.uid,
      'OOD_GID'       => Process.gid,
      'DEBUG'         => debug
    }
    env['GPG_PUBKEY'] = '/gpg.pub' if @config[:gpg_pubkey]
    env
  end
end
