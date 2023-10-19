# frozen_string_literal: true

require 'ood_packaging/utils'
require 'ood_packaging/string_ext'
require 'English'
require 'rake'
require 'rake/file_utils'
require 'yaml'

# Class to handle builds of packages from within buildbox container
class OodPackaging::Build
  include OodPackaging::Utils
  include FileUtils

  attr_accessor :build_box

  def initialize
    @build_box = OodPackaging::BuildBox.new(dist: ENV['DIST'], arch: ENV['ARCH'])
  end

  def config
    @config ||= begin
      c = packaging_config
      c.merge!(c[build_box.dist]) if c.key?(build_box.dist)
      c.transform_keys(&:to_sym)
    end
  end

  def package
    ENV['PACKAGE']
  end

  def debug?
    ENV['DEBUG'] == 'true'
  end

  def gpg_sign?
    ENV['GPG_SIGN'] == 'true'
  end

  def version
    ver = ENV['VERSION']
    return nil if ver == ''

    ver
  end

  def rpm_version
    version.gsub(/^v/, '').split('-', 2)[0]
  end

  def rpm_release
    return nil if version.nil?

    v = version.split('-', 2)
    return '1' if v.size < 2

    v[1].gsub('-', '.')
  end

  def deb_version
    version.gsub(/^v/, '').gsub('-', '.')
  end

  def deb_chlog_version
    return "#{deb_version}-#{build_box.codename}" if config[:codename_version]

    deb_version
  end

  def rpm_defines
    defines = []
    defines.concat ["--define 'git_tag #{version}'"] unless version.nil?
    defines.concat ["--define 'package_version #{rpm_version}'"] unless rpm_version.nil?
    defines.concat ["--define 'package_release #{rpm_release}'"] unless rpm_release.nil?
    defines.concat ["--define 'scl #{config[:scl]}'"] if config[:scl]
    defines
  end

  def cmd_suffix
    return '' if debug?

    ' 2>/dev/null 1>/dev/null'
  end

  def spec_dir
    @spec_dir ||= if Dir.exist?('/package/rpm')
                    '/package/rpm'
                  elsif Dir.exist?('/package/packaging/rpm')
                    '/package/packaging/rpm'
                  elsif Dir.exist?('/package/packaging')
                    '/package/packaging'
                  else
                    '/package'
                  end
  end

  def deb_build_dir
    @deb_build_dir ||= if Dir.exist?('/package/deb/build')
                         '/package/deb/build'
                       else
                         '/package/build'
                       end
  end

  def debian_dir
    @debian_dir ||= if Dir.exist?('/package/deb/debian')
                      '/package/deb/debian'
                    elsif Dir.exist?('/package/packaging/deb')
                      '/package/packaging/deb'
                    else
                      '/package/debian'
                    end
  end

  def deb_work_dir
    File.join(work_dir, deb_name)
  end

  def spec_file
    @spec_file ||= Dir["#{spec_dir}/*.spec"][0]
  end

  def output_dir
    File.join('/output', "#{build_box.dist}-#{build_box.arch}")
  end

  def work_dir
    build_box.work_dir
  end

  def packaging_config
    @packaging_config ||= begin
      path = File.join(spec_dir, 'packaging.yaml')
      path = File.join(debian_dir, 'packaging.yaml') if build_box.deb?
      if File.exist?(path)
        YAML.load_file(path)
      else
        {}
      end
    end
  end

  def deb_name
    "#{package}-#{deb_version}"
  end

  def rpms
    @rpms ||= Dir["#{output_dir}/*.rpm"].grep_v(/.src.rpm$/)
  end

  def run!
    fix_env!
    env_dump! if debug?
    bootstrap_rpm! if build_box.rpm?
    bootstrap_deb! if build_box.deb?
    install_dependencies!
    rpmbuild! if build_box.rpm?
    debuild! if build_box.deb?
    copy_output!
    show_output!
    gpg_sign! if build_box.rpm? && gpg_sign?
    sanity!
  end

  def fix_env!
    ENV.delete('GEM_PATH')
  end

  def env_dump!
    ENV.sort.to_h.each_pair do |k, v|
      puts "#{k}=#{v}"
    end
  end

  def bootstrap_rpm!
    puts '== Bootstrap RPM =='.blue
    bootstrap_gpg! if gpg_sign?
    if podman_runtime?
      puts "\tBootstrap /root".blue
      sh "cp -r #{ctr_rpmmacros} /root/"
      sh "cp -r #{ctr_gpg_dir} /root/" if gpg_sign? && build_box.dnf?
      sh "sed -i 's|/home/ood|/root|g' /root/.rpmmacros"
    end
    puts "\tBootstrap work dir".blue
    sh "mkdir -p #{work_dir}/{RPMS,SRPMS,SOURCES,SPECS,rpmbuild/BUILD}"
    bootstrap_rpm_packages! if config[:bootstrap_packages]
    bootstrap_copy_source!
    bootstrap_get_source!
  end

  def bootstrap_gpg!
    puts "\tBootstrap GPG".blue
    sh "sed -i 's|@GPG_NAME@|#{ENV['GPG_NAME']}|g' #{ctr_rpmmacros}"
    sh "gpg --batch --passphrase-file #{gpg_passphrase} --import #{gpg_private_key}#{cmd_suffix}"
    sh "sudo rpm --import #{ENV['GPG_PUBKEY']}#{cmd_suffix}" if ENV['GPG_PUBKEY']
  end

  def bootstrap_rpm_packages!
    return if config[:bootstrap_packages].nil?

    cmd = ['sudo', 'dnf'] if build_box.dnf?
    cmd = ['sudo', 'yum'] unless build_box.dnf?
    cmd.concat ['install', '-y']
    cmd.concat config[:bootstrap_packages]
    puts "\tBootstrapping additional packages".blue
    sh cmd.join(' ')
  end

  def bootstrap_copy_source!
    puts "\tCopy sources".blue
    if build_box.rpm?
      sh "find #{spec_dir} -maxdepth 1 -type f -exec cp {} #{work_dir}/SOURCES/ \\;"
      sh "find #{spec_dir} -maxdepth 1 -mindepth 1 -type d -exec cp -r {} #{work_dir}/SOURCES/ \\;"
    elsif build_box.deb?
      sh "cp -a #{deb_build_dir}/* #{work_dir}/"
    end
  end

  def bootstrap_get_source!
    if ENV['SKIP_DOWNLOAD'] == 'true'
      puts "\tSKIP_DOWNLOAD detected, skipping download sources".blue
      return
    end
    output = `spectool #{rpm_defines.join(' ')} -l -R -S #{spec_file} 2>&1 | grep 'Source0:'`.strip
    exit_code = $CHILD_STATUS.exitstatus
    if exit_code.zero?
      source = File.join(work_dir, 'SOURCES', File.basename(output))
      tar = File.join(work_dir, 'SOURCES', ENV['TAR_NAME'])
      sh "mv #{tar} #{source}" if !File.exist?(source) && File.exist?(tar)
    end
    puts "\tDownloading sources defined in #{spec_file}".blue
    sh "spectool #{rpm_defines.join(' ')} -g -R -S #{spec_file}#{cmd_suffix}"
  end

  def bootstrap_deb!
    puts '== Bootstrap DEB =='.blue
    unless Dir.exist?(work_dir)
      puts "\tCreating #{work_dir}".blue
      sh "mkdir -p #{work_dir}"
    end
    bootstrap_copy_source!
    puts "\tExtract source".blue
    Dir.chdir(work_dir) do
      sh "tar -xf #{deb_name}.tar.gz"
    end
    return unless config.fetch(:update_changelog, true)

    puts "\tBootstrap debian build files".blue
    Dir.chdir(deb_work_dir) do
      sh "dh_make -s -y --createorig -f ../#{deb_name}.tar.gz#{cmd_suffix} || true"
      sh "dch -b -v #{deb_chlog_version} --controlmaint 'Release #{deb_chlog_version}'#{cmd_suffix}"
    end
  end

  def install_dependencies!
    puts '== Install Dependencies =='.blue
    if build_box.rpm?
      install_rpm_dependencies!
    elsif build_box.deb?
      install_deb_dependencies!
    end
  end

  def install_rpm_dependencies!
    cmd = ['sudo']
    cmd.concat [build_box.package_manager, 'builddep'] if build_box.dnf?
    cmd.concat ['yum-builddep'] if build_box.package_manager == 'yum'
    cmd.concat ['-y']
    cmd.concat rpm_defines
    cmd.concat ['--spec'] if build_box.dnf?
    cmd.concat [spec_file]
    sh "#{cmd.join(' ')}#{cmd_suffix}"
  end

  def install_deb_dependencies!
    sh "sudo apt update -y#{cmd_suffix}"
    extra_depends = config.fetch(:extra_depends, nil)
    tool = [
      'DEBIAN_FRONTEND=noninteractive apt-cudf-get --solver aspcud',
      '-o APT::Get::Assume-Yes=1 -o APT::Get::Allow-Downgrades=1',
      '-o Debug::pkgProblemResolver=0 -o APT::Install-Recommends=0'
    ]
    cmd = [
      'mk-build-deps --install --remove --root-cmd sudo',
      "--tool='#{tool.join(' ')}'"
    ]
    cleanup = [
      "#{package}-build-deps*.buildinfo",
      "#{package}-build-deps*.changes"
    ]
    Dir.chdir(deb_work_dir) do
      sh "sed -i 's|@EXTRA_DEPENDS@|#{extra_depends}|g' debian/control#{cmd_suffix}" unless extra_depends.nil?
      sh "#{cmd.join(' ')}#{cmd_suffix}"
      sh "rm -f #{cleanup.join(' ')}#{cmd_suffix}"
    end
  end

  def rpmbuild!
    puts "== RPM build spec=#{spec_file} ==".blue
    cmd = ['rpmbuild', '-ba']
    cmd.concat rpm_defines
    cmd.concat [spec_file]
    sh "#{cmd.join(' ')}#{cmd_suffix}"
  end

  def debuild!
    puts "== DEB build package=#{deb_work_dir} ==".blue
    prepend_path = ''
    prepend_path = "--prepend-path=#{config[:prepend_path]}" if config[:prepend_path]
    Dir.chdir(deb_work_dir) do
      sh "debuild --no-lintian --preserve-env #{prepend_path}#{cmd_suffix}"
    end
  end

  def copy_output!
    puts '== Copy output =='.blue
    unless Dir.exist?(output_dir)
      puts "\tCreating #{output_dir}".blue
      sh "mkdir -p #{output_dir}"
    end
    if build_box.rpm?
      puts "\tcopy #{work_dir}/**/*.rpm -> #{output_dir}/".blue
      sh "find #{work_dir} -type f -name '*.rpm' -exec cp {} #{output_dir}/ \\;"
    elsif build_box.deb?
      puts "\tcopy #{work_dir}/*.deb #{output_dir}/".blue
      sh "cp #{work_dir}/*.deb #{output_dir}/"
    end
  end

  def show_output!
    puts '== Copied output =='.blue
    Dir["#{output_dir}/*"].each do |f|
      puts "\tSaved output #{f}".blue
    end
  end

  def gpg_sign!
    puts '== GPG sign RPMs =='.blue
    rpms.each do |rpm|
      puts "\tGPG signing #{rpm}".blue
      cmd = []
      # Work around differences in RHEL
      cmd.concat ['cat /dev/null | setsid'] unless build_box.dnf?
      cmd.concat ['rpmsign', '--addsign', rpm]
      sh "#{cmd.join(' ')}#{cmd_suffix}"
    end
  end

  def sanity!
    puts '== Sanity tests =='.blue
    failure = false
    if build_box.rpm? && gpg_sign?
      rpms.each do |rpm|
        puts "\tTest GPG signing #{rpm}".blue
        output = `rpm -K #{rpm} 2>&1`
        exit_code = $CHILD_STATUS.exitstatus
        puts output if debug?
        if exit_code != 0
          puts "\tGPG check failure: exit code #{exit_code}".red
          failure = true
        end
        if output !~ /(pgp|OK)/
          puts "\tRPM not GPG signed".red
          failure = true
        end
      end
    end
    exit 1 if failure
  end
end
