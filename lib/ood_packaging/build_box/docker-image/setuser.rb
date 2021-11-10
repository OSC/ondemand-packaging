#!/usr/bin/env ruby
# frozen_string_literal: true

require 'etc'

username = ARGV[0]
user = Etc.getpwnam(username)

Process.initgroups(username, user.gid)
Process::Sys.setgid(user.gid)
Process::Sys.setuid(user.uid)

ENV['USER'] = user.name
ENV['HOME'] = user.dir

exec(ARGV.drop(1).join(' '))
