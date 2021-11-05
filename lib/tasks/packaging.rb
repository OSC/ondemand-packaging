# frozen_string_literal: true

desc 'Package OnDemand'
namespace :package do
  require_relative 'package_utils'
  include PackageUtils

  desc 'Tar and zip OnDemand into packaging dir with version name v#<version>'
  task :tar, [:output_dir] do |_task, args|
    version = ENV['VERSION'] || ENV['CI_COMMIT_TAG']
    version = version.gsub(/^v/, '') unless version.nil?

    chdir src_dir do
      unless version
        latest_commit = `git rev-list --tags --max-count=1`.strip[0..6]
        latest_tag = `git describe --tags #{latest_commit}`.strip[1..-1]
        datetime = Time.now.strftime('%Y%m%d-%H%M')
        version = "#{latest_tag}-#{datetime}-#{latest_commit}"
      end

      dir = (args[:output_dir] || 'packaging/rpm').to_s.tap { |p| sh "mkdir -p #{p}" }
      sh "git ls-files | #{tar} -c --transform 's,^,ondemand-#{version}/,' -T - | gzip > #{dir}/v#{version}.tar.gz"
    end
  end

  # TODO: refactor these 2 tar tasks. Debian and RHEL expect slightly different names and
  # what's worse is the whole v prefixing mess
  task :debian_tar, [:output_dir] do |_task, args|
    dir = (args[:output_dir] || 'packaging').to_s.tap { |p| sh "mkdir -p #{p}" }
    tar_file = "#{dir}/#{ood_package_tar}"

    sh "rm #{tar_file}" if File.exist?(tar_file)
    sh "git ls-files | #{tar} -c --transform 's,^,#{versioned_ood_package}/,' -T - | gzip > #{tar_file}"
  end

  task :version do
    puts package_version
  end

  task :deb, [:dist, :version] => [:build_box] do |_task, args|
    dir = build_dir(args)
    Rake::Task['package:debian_tar'].invoke(dir)
    sh "#{tar} -xzf #{dir}/#{ood_package_tar} -C #{dir}"

    work_dir = "/build/#{versioned_ood_package}"

    base_args = ctr_run_args
    base_args.concat ['-v', "#{dir}:/build", '-w', work_dir.to_s]
    base_args.concat ['-e', "DEBUILD_DPKG_BUILDPACKAGE_OPTS='-us -uc -I -i'"]
    base_args.concat ['-e', 'HOME=/home/ood', '-e', 'USER=ood']
    base_args.concat ['-e', "VERSION=#{ENV['VERSION']}"] unless ENV['VERSION'].nil?
    base_args.concat [build_box_image(args)]
    sh "#{container_runtime} run #{base_args.join(' ')} debmake -b':ruby'"

    debuild_args = ['debuild', '--no-lintian']
    sh "#{container_runtime} run #{base_args.join(' ')} #{debuild_args.join(' ')}"
  end

  task :bootstrap_rpm, [:dist, :version] => [:verify_args] do |_task, args|
    chdir src_dir do
      build_dir(args).tap do |d|
        src_dir = "#{d}/rpmbuild/SOURCES".tap { |s| sh "mkdir -p #{s}" }
        dist_dir(args).tap { |dd| sh "mkdir -p #{dd}" }
        Rake::Task['package:tar'].invoke(src_dir)

        FileUtils.cp Dir.glob('packaging/rpm/*.{fc,te,ico,png,tar.gz}'), src_dir
        FileUtils.cp spec_location, d
      end
    end
  end

  desc 'Build an RPM'
  task :rpm, [:dist, :version] => [:build_box, :bootstrap_rpm] do |_task, args|
    dir = build_dir(args)
    image = build_box_image(args)

    base_args = ctr_run_args
    base_args.concat ['-v', "#{dir}:#{ctr_home}", '-w', "'#{ctr_home}'"]
    base_args.concat ['-e', "HOME=#{ctr_home}"]

    chdir src_dir do
      sh "#{container_runtime} run #{base_args.join(' ')} #{image} rpmbuild #{rpm_build_args.join(' ')}"
      FileUtils.cp Dir.glob("#{dir}/rpmbuild/RPMS/#{arch}/*.rpm"), dist_dir(args)
    end
  end

  namespace :rpm do
    desc 'Build nightly RPM'
    task :nightly, [:dist, :extra_args] do |_task, args|
      version_major, version_minor, version_patch = git_tag.gsub(/^v/, '').split('.', 3)
      date = Time.now.strftime('%Y%m%d')
      id = ENV['CI_PIPELINE_ID'] || Time.now.strftime('%H%M%S')
      ENV['VERSION'] = "#{version_major}.#{version_minor}.#{date}-#{id}.#{git_hash}.nightly"
      Rake::Task['package:rpm'].invoke(args[:dist], args[:extra_args])
    end
  end

  task :verify_args, [:dist, :version] do |_task, args|
    raise 'Need to specify :dist and :version' if args[:dist].nil? || args[:version].nil?
  end

  desc 'Create buildbox for Open OnDemand'
  task :build_box, [:dist, :version] => [:verify_args] do |_task, args|
    cmd = build_cmd(
      template_file("Dockerfile.#{args[:dist]}.erb"),
      build_box_image(args)
    )

    sh cmd unless image_exists?(build_box_image(args))
  end
end
