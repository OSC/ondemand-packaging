# frozen_string_literal: true

require 'bundler/setup'
Bundler.setup
require 'ood_packaging'

RSpec.configure do |config|
  config.default_formatter = 'doc'
  config.expect_with :rspec do |c|
    c.max_formatted_output_length = 1000
  end
end
