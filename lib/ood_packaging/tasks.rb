# frozen_string_literal: true

require 'ood_packaging'
require 'ood_packaging/rake_task'
require 'ood_packaging/utils'

namespace :ood_packaging do
  include OodPackaging::Utils

  namespace :buildbox do
    desc 'Build buildbox image'
    task :build, [:dist] do |_task, args|
      @build_box = OodPackaging::BuildBox.new(args)
      @build_box.build!
    end

    desc 'Push buildbox image'
    task :push, [:dist] do |_task, args|
      @build_box = OodPackaging::BuildBox.new(args)
      @build_box.push!
    end

    desc 'Save buildbox image'
    task :save, [:dist, :path] do |_task, args|
      @build_box = OodPackaging::BuildBox.new(args)
      @build_box.save!(args[:path])
    end
  end

  namespace :package do
    desc 'Build a package (INSIDE CONTAINER ONLY)'
    task :build do
      OodPackaging::Build.new.run!
    end

    OodPackaging::RakeTask.new(:internal, [:package, :dist]) do |t, args|
      name = args[:package].split(':').last
      t.package = File.join(proj_root, 'packages', name)
      t.dist = args[:dist]
      t.version = OodPackaging.package_version(name, args[:dist])
      t.work_dir = File.join(proj_root, 'tmp/work')
      t.output_dir = File.join(proj_root, 'tmp/output')
    end

    desc 'Package ondemand-release'
    task :'ondemand-release', [:dist] do |t, args|
      ENV['OOD_PACKAGING_GPG_SIGN'] = 'false'
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist])
    end

    desc 'Package ondemand-release-latest'
    task :'ondemand-release-latest', [:dist] do |t, args|
      ENV['OOD_PACKAGING_GPG_SIGN'] = 'false'
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist])
    end

    desc 'Package ondemand-release'
    task :'ondemand-runtime', [:dist] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist])
    end

    desc 'Package passenger'
    task :passenger, [:dist] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist])
    end

    desc 'Package cjose'
    task :cjose, [:dist] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist])
    end

    desc 'Package mod_auth_openidc'
    task :mod_auth_openidc, [:dist] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist])
    end

    desc 'Package sqlite'
    task :sqlite, [:dist] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist])
    end

    desc 'Package ondemand_exporter'
    task :ondemand_exporter, [:dist] do |t, args|
      Rake::Task['ood_packaging:package:internal'].invoke(t.name, args[:dist])
    end
  end
end