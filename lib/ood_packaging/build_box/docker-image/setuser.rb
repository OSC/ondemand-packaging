#!/usr/bin/env ruby
# frozen_string_literal: true

require 'etc'

user = Etc.getpwnam('ood')

Process.initgroups('ood', user.gid)
Process::Sys.setgid(user.gid)
Process::Sys.setuid(user.uid)

ENV['USER'] = user.name
ENV['HOME'] = user.dir

exec(ARGV.join(' '))
