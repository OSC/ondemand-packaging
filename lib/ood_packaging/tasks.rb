# frozen_string_literal: true

require 'ood_packaging'

namespace :ood_packaging do
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
    task :push, [:dist, :path] do |_task, args|
      @build_box = OodPackaging::BuildBox.new(args)
      @build_box.save!(path)
    end
  end

  namespace :package do
    desc 'Build a package (INSIDE CONTAINER ONLY)'
    task :build do
      OodPackaging::Build.new.run!
    end
  end
end
