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

    desc 'Package ondemand-release'
    OodPackaging::RakeTask.new(:'ondemand-release', [:dist]) do |t, args|
      t.package = File.join(proj_root, 'packages/ondemand-release')
      t.dist = args[:dist]
      t.version = OodPackaging.package_version('ondemand-release', args[:dist])
      t.gpg_sign = false
      t.work_dir = File.join(proj_root, 'tmp/work')
      t.output_dir = File.join(proj_root, 'tmp/output')
    end

    desc 'Package ondemand-release-latest'
    OodPackaging::RakeTask.new(:'ondemand-release-latest', [:dist]) do |t, args|
      t.package = File.join(proj_root, 'packages/ondemand-release-latest')
      t.dist = args[:dist]
      t.version = OodPackaging.package_version('ondemand-release-latest', args[:dist])
      t.gpg_sign = false
      t.work_dir = File.join(proj_root, 'tmp/work')
      t.output_dir = File.join(proj_root, 'tmp/output')
    end

    desc 'Package ondemand-release'
    OodPackaging::RakeTask.new(:'ondemand-runtime', [:dist]) do |t, args|
      t.package = File.join(proj_root, 'packages/ondemand-runtime')
      t.dist = args[:dist]
      t.version = OodPackaging.package_version('ondemand-runtime', args[:dist])
      t.work_dir = File.join(proj_root, 'tmp/work')
      t.output_dir = File.join(proj_root, 'tmp/output')
    end

    desc 'Package passenger'
    OodPackaging::RakeTask.new(:passenger, [:dist]) do |t, args|
      t.package = File.join(proj_root, 'packages/passenger')
      t.dist = args[:dist]
      t.version = OodPackaging.package_version('passenger', args[:dist])
      t.work_dir = File.join(proj_root, 'tmp/work')
      t.output_dir = File.join(proj_root, 'tmp/output')
    end

    desc 'Package cjose'
    OodPackaging::RakeTask.new(:cjose, [:dist]) do |t, args|
      t.package = File.join(proj_root, 'packages/cjose')
      t.dist = args[:dist]
      t.version = OodPackaging.package_version('cjose', args[:dist])
      t.work_dir = File.join(proj_root, 'tmp/work')
      t.output_dir = File.join(proj_root, 'tmp/output')
    end

    desc 'Package mod_auth_openidc'
    OodPackaging::RakeTask.new(:mod_auth_openidc, [:dist]) do |t, args|
      t.package = File.join(proj_root, 'packages/mod_auth_openidc')
      t.dist = args[:dist]
      t.version = OodPackaging.package_version('mod_auth_openidc', args[:dist])
      t.work_dir = File.join(proj_root, 'tmp/work')
      t.output_dir = File.join(proj_root, 'tmp/output')
    end

    desc 'Package sqlite'
    OodPackaging::RakeTask.new(:sqlite, [:dist]) do |t, args|
      t.package = File.join(proj_root, 'packages/sqlite')
      t.dist = args[:dist]
      t.version = OodPackaging.package_version('sqlite', args[:dist])
      t.work_dir = File.join(proj_root, 'tmp/work')
      t.output_dir = File.join(proj_root, 'tmp/output')
    end

    desc 'Package ondemand_exporter'
    OodPackaging::RakeTask.new(:ondemand_exporter, [:dist]) do |t, args|
      t.package = File.join(proj_root, 'packages/ondemand_exporter')
      t.dist = args[:dist]
      t.version = OodPackaging.package_version('ondemand_exporter', args[:dist])
      t.work_dir = File.join(proj_root, 'tmp/work')
      t.output_dir = File.join(proj_root, 'tmp/output')
    end
  end
end
