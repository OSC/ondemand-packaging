# frozen_string_literal: true

# Version code for OodPackaging
module OodPackaging
  VERSION = '0.16.1'
  PACKAGE_VERSION = {
    'ondemand-release'        => {
      '(ubuntu|debian)' => '4.0.0',
      'default'         => '4.0'
    },
    'ondemand-release-latest' => {
      '(ubuntu|debian)' => '5',
      'default'         => '1-8'
    },
    'ondemand-runtime'        => '4.0.1',
    'scl-utils'               => '2.0.3',
    'passenger'               => '6.0.23',
    'cjose'                   => '0.6.1',
    'mod_auth_openidc'        => '2.4.14.1',
    'ondemand_exporter'       => '0.10.0',
    'ondemand-compute'        => {
      '(ubuntu|debian)' => '4.0.0',
      'default'         => '4.0.0'
    },
    'python-websockify'       => '0.11.0',
    'turbovnc'                => '3.1.1'
  }.freeze

  def self.package_version(package, dist)
    return PACKAGE_VERSION[package] if PACKAGE_VERSION[package].is_a?(String)

    PACKAGE_VERSION[package].each_pair do |k, v|
      return v if dist =~ /#{k}/
    end
    PACKAGE_VERSION[package]['default']
  end
end
