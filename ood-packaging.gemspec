# frozen_string_literal: true

lib = File.expand_path('lib', __dir__)
$LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)
require 'ood_packaging/version'

Gem::Specification.new do |spec|
  spec.name          = 'ood_packaging'
  spec.version       = OodPackaging::VERSION
  spec.authors       = ['Trey Dockendorf', 'Jeff Ohrstrom']
  spec.email         = ['tdockendorf@osc.edu', 'johrstrom@osc.edu']

  spec.summary       = 'Open OnDemand packaging library'
  spec.description   = 'Open OnDemand packaging library provides Rake tasks like package:rpm and pacakge:deb'
  spec.homepage      = 'https://github.com/OSC/ood-packaging'
  spec.license       = 'MIT'

  spec.files         = `git ls-files -z`.split("\x0").select do |f|
    f.match(%r{^lib/})
  end
  spec.bindir        = 'bin'
  spec.executables   = []
  spec.require_paths = ['lib']
  spec.required_ruby_version = '>= 2.2.0'

  spec.add_runtime_dependency 'rake', '~> 13.0.1'
end
