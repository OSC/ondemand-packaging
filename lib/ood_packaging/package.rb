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
    @build_box = OodPackaging::BuildBox.new(config)
    @package = config[:package]
    @version = config[:version]
    @clean_work_dir = config[:clean_work_dir].nil? ? true : config[:clean_work_dir]
    @clean_output_dir = config[:clean_output_dir].nil? ? true : config[:clean_output_dir]
    @gpg_name = @config[:gpg_name].nil? ? 'OnDemand Release Signing Key' : @config[:gpg_name]
    raise ArgumentError, 'Package is required' if @package.nil?
    raise ArgumentError, 'Version is required' if @version.nil?
    raise ArgumentError, "Package #{@package} is not a directory" unless Dir.exist?(@package)
    raise ArgumentError, "Package #{@package} is not an absolute path" unless (Pathname.new @package).absolute?
  end

  def container_name
    @container_name ||= SecureRandom.uuid
  end

  def debug
    @config[:debug].nil? ? false : @config[:debug]
  end

  def attach
    @config[:attach].nil? ? false : @config[:attach]
  end

  def work_dir
    @work_dir ||= File.expand_path(@config[:work_dir])
  end

  def output_dir
    @output_dir ||= File.expand_path(@config[:output_dir])
  end

  def gpg_files
    [
      OpenStruct.new(private_key: File.join(proj_root, 'ondemand.sec'), passphrase: File.join(proj_root, '.gpgpass')),
      OpenStruct.new(private_key: File.join(@package, 'ondemand.sec'), passphrase: File.join(@package, '.gpgpass')),
      OpenStruct.new(private_key: @config[:gpg_private_key], passphrase: @config[:gpg_passphrase]),
      OpenStruct.new(private_key: ENV['OOD_PACKAGING_GPG_PRIVATE_KEY'],
                     passphrase:  ENV['OOD_PACKAGING_GPG_PASSPHRASE'])
    ].each do |gpg|
      next if gpg.private_key.nil? || gpg.passphrase.nil?
      return gpg if File.exist?(gpg.private_key) && File.exist?(gpg.passphrase)
    end
    nil
  end

  def gpg_sign
    return false if @config[:gpg_sign] == false

    !gpg_files.nil?
  end

  def container_init
    '/sbin/init'
  end

  def exec_launchers
    [
      File.join(ctr_scripts_dir, 'inituidgid.sh'),
      File.join(ctr_scripts_dir, 'setuser.rb'),
      ctr_user
    ]
  end

  def exec_rake
    cmd = exec_launchers
    cmd.concat ['rake']
    cmd.concat ['-q'] unless debug
    cmd.concat ['-f', File.join(ctr_scripts_dir, 'Rakefile'), 'ood_packaging:package:build']
    cmd
  end

  def exec_attach
    cmd = exec_launchers
    cmd.concat ['/bin/bash']
    cmd
  end

  def clean!
    sh "rm -rf #{work_dir}", verbose: debug if @clean_work_dir
    sh "rm -rf #{output_dir}", verbose: debug if @clean_output_dir
  end

  def bootstrap!
    sh "mkdir -p #{work_dir}", verbose: debug
    sh "mkdir -p #{output_dir}", verbose: debug
  end

  def run!
    clean!
    bootstrap!
    container_start!
    container_exec!(exec_rake)
  rescue RuntimeError
    # ret = 1
    puts "Build FAILED package=#{@package} dist=#{@build_box.dist}".red
    raise
  else
    puts "Build SUCCESS: package=#{@package} dist=#{@build_box.dist}".green
  ensure
    container_exec!(exec_attach) if attach
    container_kill! if container_running?
  end

  def container_running?
    `#{container_runtime} inspect #{container_name} 2>/dev/null 1>/dev/null`
    $CHILD_STATUS.success?
  end

  def container_start!
    cmd = [container_runtime, 'run', '--detach', '--rm']
    cmd.concat ['--name', container_name]
    cmd.concat ['--privileged', '--cap-add=SYS_ADMIN']
    cmd.concat rt_specific_flags
    cmd.concat ['-v', "#{@package}:/package:ro"]
    cmd.concat ['-v', "#{@config[:gpg_pubkey]}:/gpg.pub:ro"] if @config[:gpg_pubkey]
    cmd.concat ['-v', "#{work_dir}:/work"]
    cmd.concat ['-v', "#{output_dir}:/output"]
    if gpg_sign
      cmd.concat ['-v', "#{gpg_files.private_key}:#{gpg_private_key}:ro"]
      cmd.concat ['-v', "#{gpg_files.passphrase}:#{gpg_passphrase}:ro"]
    end
    cmd.concat [@build_box.image_tag, container_init]
    cmd.concat ['1>/dev/null'] unless debug
    puts "Starting container #{container_name} using image #{@build_box.image_tag}".blue
    sh cmd.join(' '), verbose: debug
  end

  def container_exec!(exec_cmd)
    cmd = [container_runtime, 'exec', '-i', '-t']
    container_env.each_pair do |k, v|
      cmd.concat ['-e', "'#{k}=#{v}'"] unless v.nil?
    end
    cmd.concat [container_name]
    cmd.concat exec_cmd
    puts "Build STARTED: package=#{@package} dist=#{@build_box.dist} exec=#{exec_cmd[-1]}".blue
    sh cmd.join(' '), verbose: debug
  end

  def container_kill!
    puts "Killing container #{container_name}".blue
    cmd = [container_runtime, 'kill', container_name]
    cmd.concat ['1>/dev/null', '2>/dev/null'] unless debug
    sh cmd.join(' '), verbose: debug
  end

  def container_env
    env = {
      'DIST'          => @build_box.dist,
      'PACKAGE'       => @package,
      'GPG_SIGN'      => gpg_sign,
      'GPG_NAME'      => @gpg_name,
      'VERSION'       => @version,
      'SKIP_DOWNLOAD' => @config[:skip_download],
      'OOD_UID'       => Process.uid,
      'OOD_GID'       => Process.gid,
      'DEBUG'         => debug
    }
    env['GPG_PUBKEY'] = '/gpg.pub' if @config[:gpg_pubkey]
    env
  end
end