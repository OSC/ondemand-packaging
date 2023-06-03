# frozen_string_literal: true

# Handle options for OodPackaging
module OodPackaging
  OPTIONS = [:package, :version, :dist, :arch, :work_dir, :clean_work_dir, :output_dir, :clean_output_dir, :tar,
             :tar_only, :skip_download, :gpg_sign, :gpg_name, :gpg_pubkey, :gpg_private_key, :gpg_passphrase,
             :debug, :attach].freeze
end
