# frozen_string_literal: true

require 'erb'

# Shared utility functions
module OodPackaging::Utils
  def proj_root
    File.expand_path(File.join(File.dirname(__FILE__), '../..'))
  end

  def podman_runtime?
    @podman_runtime ||= ENV['CONTAINER_RT'] == 'podman'
  end

  def docker_runtime?
    !podman_runtime?
  end

  def container_runtime
    podman_runtime? ? 'podman' : 'docker'
  end

  def rt_specific_flags
    if podman_runtime?
      # SELinux doesn't like it if you're mounting from $HOME
      ['--security-opt', 'label=disable', '--userns=keep-id']
    else
      []
    end
  end

  def template_file(filename)
    cwd = File.expand_path(__dir__).to_s
    src = File.join(cwd, filename)
    dest = File.join(cwd, filename.gsub('.erb', ''))
    content = ERB.new(File.read(src), nil, '-').result(binding)
    File.open(dest, 'w') { |f| f.write(content) }
    dest
  end

  def ruby_version
    '2.7'
  end

  def scl_ruby
    "rh-ruby#{ruby_version.tr('.', '')}"
  end

  def ctr_scripts_dir
    '/ondemand-packaging'
  end

  def gpg_private_key
    File.join(ctr_scripts_dir, 'ondemand.sec')
  end

  def gpg_passphrase
    File.join(ctr_scripts_dir, '.gpgpass')
  end

  def ctr_user
    'ood'
  end

  def ctr_home
    File.join('/home', ctr_user)
  end

  def ctr_rpmmacros
    File.join(ctr_home, '.rpmmacros')
  end

  def ctr_gpg_dir
    File.join(ctr_home, '.gnupg')
  end
end