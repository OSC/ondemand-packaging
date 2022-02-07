# build manpages
directory "lib/bundler/man"

sources = Dir["man/*.ronn"].map {|f| File.basename(f, ".ronn") }
sources.map do |basename|
  ronn = "man/#{basename}.ronn"
  roff = "lib/bundler/man/#{basename}"

  file roff => ["lib/bundler/man", ronn] do
    sh "#{Gem.ruby} -S ronn --roff --pipe #{ronn} > #{roff}"
  end

  file "#{roff}.txt" => roff do
    sh "groff -Wall -mtty-char -mandoc -Tascii #{roff} | col -b > #{roff}.txt"
  end

  task :default => "#{roff}.txt"
end
task :install do
  # handled by dh_installman
end
task :clean do
  # not required
end
