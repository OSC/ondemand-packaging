# frozen_string_literal: true

require 'English'
require 'erb'
require 'tempfile'

module PackageUtils
  def version
    @version ||= if !ENV['VERSION']
                   tag? ? git_tag : "#{git_tag}-#{git_hash}"
                 else
                   ENV['VERSION'].to_s
                 end
  end

  def build_timestamp
    @build_timestamp ||= Time.now.strftime('%s')
  end

  def git_hash
    @git_hash ||= `git rev-parse HEAD`.strip[0..6]
  end

  def git_tag
    @git_tag ||= `git describe --tags --abbrev=0`.chomp
  end

  def numeric_tag
    @numeric_tag ||= git_tag.delete_prefix('v')
  end

  def tag?
    @tag ||= `git describe --exact-match --tags HEAD 2>/dev/null`.to_s != ''
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

  def tar
    @tar ||= begin
      `which gtar 1>/dev/null 2>&1`
      $CHILD_STATUS.success? ? 'gtar' : 'tar'
    end
  end

  def src_dir
    ENV['OOD_SRC_DIR'] || '.'
  end

  def user
    @user ||= Etc.getpwnam(Etc.getlogin)
  end

  def build_dir(args)
    @build_dir ||= "#{src_dir}/build/#{build_box_image(args).gsub(':', '-')}".tap { |d| sh "mkdir -p #{d}" }
  end

  # TODO: continue vendor/ convention? Seems as good as any other name.
  def vendor_src_dir
    'vendor/ood/src'.tap { |p| sh "mkdir -p #{p}" }
  end

  def vendor_build_dir
    'vendor/ood/build'.tap { |p| sh "mkdir -p #{p}" }
  end

  def dist_dir(args)
    dist = args[:dist].to_s
    version = args[:version].to_s

    if dist == 'el'
      "dist/#{dist}#{version}"
    else
      # don't know what the debian format should be
      "dist/#{dist}#{version}"
    end
  end

  def known_images
    {
      'ubuntu-20.04': '1'
    }.freeze
  end

  def build_box_image(args)
    base_name = "#{args[:dist]}-#{args[:version]}"
    @version_lookup ||= Hash.new('1').merge(known_images)

    "#{build_box_name}:#{base_name}-#{@version_lookup[base_name.to_sym]}"
  end

  def build_box_name
    ENV['OOD_BUILD_BOX'] || 'ood-buildbox'
  end

  def image_exists?(image_name)
    `#{container_runtime} inspect --type image --format exists #{image_name} || true`.chomp.eql?('exists')
  end

  def build_cmd(file, image)
    args = [container_runtime, 'build', '-t', image, '-f', file]
    args.concat '.' if docker_runtime?
    args.join(' ')
  end

  def template_file(filename)
    cwd = File.expand_path(__dir__).to_s
    content = File.read("#{cwd}/templates/#{filename}")
    content = ERB.new(content, nil, '-').result(binding)

    begin
      t = Tempfile.new('ood-docker')
      t.write(content)
      t.path
    ensure
      t.close
    end
  end

  def ctr_home
    "/home/#{ctr_user}"
  end

  def ctr_user
    'ood'
  end

  def ctr_run_args
    [
      '--rm', '--user', "#{ctr_user}:#{ctr_user}",
      '-e', 'LC_CTYPE=en_US.UTF-8'
    ].concat(rt_specific_flags)
  end

  def rt_specific_flags
    if podman_runtime?
      # SELinux doesn't like it if you're mounting from $HOME
      ['--security-opt', 'label=disable', '--userns=keep-id']
    else
      []
    end
  end

  def arch
    'x86_64'
  end

  def spec_location
    sf = Dir.glob('packaging/rpm/*.spec').first
    raise StandardError, 'Cannot find spec file in packaging/rpm' if sf.nil?

    sf
  end

  def spec_file
    File.basename(spec_location)
  end

  def rpm_build_args
    [git_tag_define, version_define, '-ba', '--nodeps', '-vv', spec_file]

    # if git_prerelease_tag.size >= 2
    #   git_prerelease_verison = git_prerelease_tag[0]
    #   git_prerelease_verison = git_prerelease_verison[1..-1] if git_prerelease_verison.start_with?('v')
    #   version_define = "--define 'package_version #{git_prerelease_verison}'"
    #   if git_tag.size >= 2
    #     prerelease = git_prerelease_tag[1].gsub('-', '.')
    #     release_define = "--define 'package_release 0.#{prerelease}'"
    #   else
    #     release_define = "--define 'package_release 0.#{git_prerelease_tag[1]}.1'"
    #   end
    # else
    #   version_define = "--define 'package_version #{git_tag_version}'"
    #   release_define = if git_tag.size >= 2
    #                      "--define 'package_release #{git_tag[1]}'"
    #                    else
    #                      ''
    #                    end
    # end
  end

  def version_define
    git_tag = version.split('-')
    git_tag_version = git_tag[0]
    git_tag_version = git_tag_version[1..-1] if git_tag_version.start_with?('v')

    "--define 'package_version #{git_tag_version}'"
  end

  def git_tag_define
    "--define 'git_tag #{version}'"
  end
end
