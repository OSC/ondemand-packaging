# frozen_string_literal: true

# Version code for OodPackaging
module OodPackaging
  VERSION = '0.0.1'
  PACKAGE_VERSION = {
    'ondemand-release'        => {
      '(ubuntu|debian)' => '2.1.0',
      'default'         => '2.1'
    },
    'ondemand-release-latest' => {
      '(ubuntu|debian)' => '1',
      'default'         => '1-6'
    },
    'ondemand-runtime'        => '2.1',
    'passenger'               => '6.0.11',
    'cjose'                   => '0.6.1',
    'mod_auth_openidc'        => '2.4.5',
    'sqlite'                  => '3.26.0-4',
    'ondemand_exporter'       => '0.9.0',
    'python-websockify'       => '0.8.0',
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