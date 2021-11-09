# frozen_string_literal: true

require 'bundler/setup'
Bundler.setup
require 'ood_packaging'

RSpec.configure do |config|
  config.default_formatter = 'doc'
end
