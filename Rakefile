require 'ood_packaging/tasks'
require 'bundler/gem_tasks'

begin
  require 'rspec/core/rake_task'
  require 'rubocop/rake_task'

  RSpec::Core::RakeTask.new(:spec)
  RuboCop::RakeTask.new(:rubocop) do |t, args|
    t.patterns = [
      'bin/*',
      'lib/**/*.rb',
      'spec/**/*.rb',
    ]
    t.requires << 'rubocop-rspec'
  end

  task :default => [:spec, :rubocop]
rescue LoadError
end
