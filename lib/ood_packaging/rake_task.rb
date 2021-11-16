# frozen_string_literal: true

require 'ood_packaging/package'
require 'ood_packaging/utils'
require 'rake'
require 'rake/tasklib'

# Define OodPackaging rake task library
class OodPackaging::RakeTask < ::Rake::TaskLib
  include ::Rake::DSL if defined?(::Rake::DSL)
  include OodPackaging::Utils

  OPTIONS = [:package, :version, :dist, :work_dir, :clean_work_dir, :output_dir, :clean_output_dir, :tar,
             :skip_download, :gpg_sign, :gpg_name, :gpg_pubkey, :gpg_private_key, :gpg_passphrase,
             :debug, :attach].freeze
  OPTIONS.each do |o|
    attr_accessor o.to_sym
  end

  def initialize(*args, &task_block)
    super()
    @name = args.shift || :package

    define(args, &task_block)
  end

  def define(args, &task_block)
    desc 'Build package' unless ::Rake.application.last_description

    task @name, *args do |_, task_args|
      task_block&.call(*[self, task_args].slice(0, task_block.arity))
      config = {}
      OPTIONS.each do |o|
        v = instance_variable_get("@#{o}")
        config[o.to_sym] = v unless v.nil?
      end
      OodPackaging::Package.new(config).run!
    end
  end
end
