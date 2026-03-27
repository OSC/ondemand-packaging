# frozen_string_literal: true

# Version code for OodPackaging
module OodPackaging
  VERSION = '0.20.0'
  PACKAGE_VERSION = {
    'ondemand-release'        => {
      '(ubuntu|debian)' => '4.2.0',
      'default'         => '4.2'
    },
    'ondemand-release-latest' => {
      '(ubuntu|debian)' => '6',
      'default'         => '1-8'
    },
    'ondemand-runtime'        => '4.2.0-1',
    'scl-utils'               => '2.0.3',
    'passenger'               => {
      '(ubuntu|debian)' => '6.1.2',
      'default'         => '6.1.2-1'
    },
    'ondemand_exporter'       => '0.11.2',
    'ondemand-compute'        => {
      '(ubuntu|debian)' => '4.2.0',
      'default'         => '4.2.0'
    },
    'python-websockify'       => '0.11.0-2',
    'turbovnc'                => '3.2.1'
  }.freeze

  def self.package_version(package, dist)
    return PACKAGE_VERSION[package] if PACKAGE_VERSION[package].is_a?(String)

    PACKAGE_VERSION[package].each_pair do |k, v|
      return v if dist =~ /#{k}/
    end
    PACKAGE_VERSION[package]['default']
  end
end
