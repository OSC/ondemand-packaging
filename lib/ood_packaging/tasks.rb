# frozen_string_literal: true

require 'ood_packaging'
require 'ood_packaging/rake_task'
require 'ood_packaging/utils'

namespace :ood_packaging do
  include OodPackaging::Utils

  desc 'Set version'
  task :version, [:version] do |_task, args|
    version_file = File.join(proj_root, 'lib/ood_packaging/version.rb')
    version = args[:version].gsub(/^v/, '')
    sh "#{sed} -i -r \"s|  VERSION =.*|  VERSION = '#{version}'|g\" #{version_file}"
    sh 'bundle install'
  end

  namespace :buildbox do
    desc 'Build buildbox image'
    task :build, [:dist, :arch] do |_task, args|
      @build_box = OodPackaging::BuildBox.new(args)
      @build_box.build!
    end

    desc 'Push buildbox image'
    task :push, [:dist, :arch] do |_task, args|
      @build_box = OodPackaging::BuildBox.new(args)
      @build_box.push!
    end

    desc 'Pull buildbox image'
    task :pull, [:dist, :arch] do |_task, args|
      @build_box = OodPackaging::BuildBox.new(args)
      @build_box.pull!
    end

    desc 'Save buildbox image'
    task :save, [:dist, :arch, :path] do |_task, args|
      @build_box = OodPackaging::BuildBox.new(args)
      @build_box.save!(args[:path])
    end
  end

  namespace :package do
    desc 'Build a package (INSIDE CONTAINER ONLY)'
    task :build do
      OodPackaging::Build.new.run!
    end

    OodPackaging::RakeTask.new(:internal, [:package, :dist, :arch]) do |t, args|
      name = args[:package].split(':').last
      t.package = File.join(proj_root, 'packages', name)
      dist = args[:dist] || ENV.fetch('OOD_PACKAGING_DIST', nil)
      arch = args[:arch] || ENV['OOD_PACKAGING_ARCH'] || 'x86_64'
      t.dist = dist
      t.arch = arch
      t.version = OodPackaging.package_version(name, dist)
      t.work_dir = File.join(proj_root, 'tmp/work')
      t.output_dir = File.join(proj_root, 'tmp/output')
    end

    desc 'Package ondemand-release'
    task :'ondemand-release', [:dist, :arch] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist], args[:arch])
    end

    desc 'Package ondemand-release-latest'
    task :'ondemand-release-latest', [:dist, :arch] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist], args[:arch])
    end

    desc 'Package ondemand-runtime'
    task :'ondemand-runtime', [:dist, :arch] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist], args[:arch])
    end

    desc 'Package scl-utils'
    task :'scl-utils', [:dist, :arch] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist], args[:arch])
    end

    desc 'Package passenger'
    task :passenger, [:dist, :arch] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist], args[:arch])
    end

    desc 'Package ondemand_exporter'
    task :ondemand_exporter, [:dist, :arch] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist], args[:arch])
    end

    desc 'Package ondemand-compute'
    task :'ondemand-compute', [:dist, :arch] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist], args[:arch])
    end

    desc 'Package python-websockify'
    task :'python-websockify', [:dist, :arch] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist], args[:arch])
    end

    desc 'Package turbovnc'
    task :turbovnc, [:dist, :arch] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist], args[:arch])
    end
  end
end
