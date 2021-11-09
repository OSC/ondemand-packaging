# frozen_string_literal: true

require 'erb'
require 'tempfile'

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
    content = File.read(File.join(cwd, filename))
    content = ERB.new(content, nil, '-').result(binding)

    begin
      t = Tempfile.new('ood_packaging')
      t.write(content)
      t.path
    ensure
      t.close
    end
  end

  def gpg_private_key
    '/ondemand-packaging/ondemand.sec'
  end

  def gpg_passphrase
    '/ondemand-packaging/.gpgpass'
  end
end
