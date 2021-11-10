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
    @build_box = OodPackaging::BuildBox.new(dist: ENV['DIST'])
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
    ENV['VERSION'].gsub(/^v/, '')
  end

  def rpm_version
    version.split('-', 2)[0]
  end

  def rpm_release
    v = version.split('-', 2)
    return '1' if v.size < 2

    v[1]
  end

  def rpm_defines
    defines = ["--define 'git_tag #{ENV['VERSION']}'"]
    defines.concat ["--define 'package_version #{rpm_version}'"]
    defines.concat ["--define 'package_release #{rpm_release}'"]
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
                    else
                      '/package/debian'
                    end
  end

  def spec_file
    @spec_file ||= Dir["#{spec_dir}/*.spec"][0]
  end

  def output_dir
    File.join('/output', build_box.dist)
  end

  def work_dir
    File.join('/work', build_box.dist)
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

  def package_name
    name = File.basename(package)
    if name =~ /deb|rpm/
      name = if File.basename(File.dirname(package)) == 'packages'
               File.basename(File.dirname(File.dirname(package)))
             else
               File.basename(File.dirname(package))
             end
    end
    name
  end

  def deb_name
    "#{package_name}-#{version}"
  end

  def rpms
    @rpms ||= Dir["#{output_dir}/*.rpm"].grep_v(/.src.rpm$/)
  end

  def run!
    env_dump! if debug?
    bootstrap_rpm! if build_box.rpm?
    bootstrap_deb! if build_box.deb?
    install_dependencies!
    rpmbuild! if build_box.rpm?
    debuild! if build_box.deb?
    copy_output!
    gpg_sign! if build_box.rpm? && gpg_sign?
    sanity!
  end

  def env_dump!
    ENV.sort.to_h.each_pair do |k, v|
      puts "#{k}=#{v}"
    end
  end

  def bootstrap_rpm!
    puts '== Bootstrap RPM =='.blue
    puts "\tClean build environment".blue
    sh 'rm -rf /home/ood/rpmbuild/*/*'
    if gpg_sign?
      puts "\tBootstrap GPG".blue
      sh "sed -i 's|@GPG_NAME@|#{ENV['GPG_NAME']}|g' ~/.rpmmacros"
      sh 'rm -f ~/.gnupg/*.gpg*'
      sh "gpg --batch --passphrase-file #{gpg_passphrase} --import #{gpg_private_key}#{cmd_suffix}"
      sh "sudo rpm --import #{ENV['GPG_PUBKEY']}#{cmd_suffix}" if ENV['GPG_PUBKEY']
    end
    puts "\tBootstrap work dir".blue
    sh "rpmdev-setuptree#{cmd_suffix}"
    puts "\tCopy sources".blue
    sh "find #{spec_dir} -maxdepth 1 -type f -exec cp {} #{work_dir}/SOURCES/ \\;"
    sh "find #{spec_dir} -maxdepth 1 -mindepth 1 -type d -exec cp -r {} #{work_dir}/SOURCES/ \\;"
    if ENV['SKIP_DOWNLOAD'] == 'true'
      puts "\tSKIP_DOWNLOAD detected, skipping download sources".blue
    else
      puts "\tDownloading sources defined in #{spec_file}".blue
      sh "spectool #{rpm_defines.join(' ')} -g -R -S #{spec_file}#{cmd_suffix}"
    end
  end

  def bootstrap_deb!
    puts '== Bootstrap DEB =='.blue
    unless Dir.exist?(work_dir)
      puts "\tCreating #{work_dir}".blue
      sh "mkdir -p #{work_dir}"
    end
    puts "\t cp #{deb_build_dir}/* #{work_dir}/".blue
    sh "cp -a #{deb_build_dir}/* #{work_dir}/"
    puts "\tExtract source".blue
    Dir.chdir(work_dir) do
      sh "tar -xf #{deb_name}.tar.gz"
    end
    puts "\tBootstrap debian build files".blue
    Dir.chdir(File.join(work_dir, deb_name)) do
      sh "dh_make -s -y --createorig -f ../#{deb_name}.tar.gz#{cmd_suffix} || true"
      sh "dch -b -v #{version} 'Release #{version}'#{cmd_suffix}"
    end
  end

  def install_dependencies!
    puts '== Install Dependencies =='.blue
    if build_box.rpm?
      cmd = ['sudo']
      cmd.concat [build_box.package_manager, 'builddep'] if build_box.dnf?
      cmd.concat ['yum-builddep'] if build_box.package_manager == 'yum'
      cmd.concat ['-y']
      cmd.concat rpm_defines
      cmd.concat ['--spec'] if build_box.dnf?
      cmd.concat [spec_file]
      sh "#{cmd.join(' ')}#{cmd_suffix}"
    elsif build_box.deb?
      cmd = [
        'mk-build-deps --install --remove --root-cmd sudo',
        "--tool='apt-get -o Debug::pkgProblemResolver=yes --no-install-recommends --yes'"
      ]
      Dir.chdir(File.join(work_dir, deb_name)) do
        sh "#{cmd.join(' ')}#{cmd_suffix}"
      end
    end
  end

  def rpmbuild!
    puts "== RPM build spec=#{spec_file} ==".blue
    cmd = ['rpmbuild', '-ba']
    cmd.concat ['-vv'] if debug?
    cmd.concat [spec_file]
    sh "#{cmd.join(' ')}#{cmd_suffix}"
  end

  def debuild!
    prepend_path = ''
    prepend_path = "--prepend-path=#{config['prepend_path']}" if packaging_config['prepend_path']
    Dir.chdir(File.join(work_dir, deb_name)) do
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
