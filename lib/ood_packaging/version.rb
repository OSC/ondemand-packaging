# frozen_string_literal: true

# Version code for OodPackaging
module OodPackaging
  VERSION = '0.14.0'
  PACKAGE_VERSION = {
    'ondemand-release'        => {
      '(ubuntu|debian)' => '3.1.1',
      'default'         => '3.1'
    },
    'ondemand-release-latest' => {
      '(ubuntu|debian)' => '3',
      'default'         => '1-8'
    },
    'ondemand-runtime'        => '3.1.4',
    'scl-utils'               => '2.0.3',
    'passenger'               => '6.0.17',
    'cjose'                   => '0.6.1',
    'mod_auth_openidc'        => '2.4.14.1',
    'ondemand_exporter'       => '0.10.0',
    'ondemand-compute'        => {
      '(ubuntu|debian)' => '3.1.0',
      'default'         => '3.1.0'
    },
    'python-websockify'       => '0.10.0',
    'turbovnc'                => '2.2.5'
  }.freeze

  def self.package_version(package, dist)
    return PACKAGE_VERSION[package] if PACKAGE_VERSION[package].is_a?(String)

    PACKAGE_VERSION[package].each_pair do |k, v|
      return v if dist =~ /#{k}/
    end
    PACKAGE_VERSION[package]['default']
  end
end
