# frozen_string_literal: true

require 'spec_helper'
require 'ood_packaging/rake_task'

describe OodPackaging::RakeTask do
  let(:tmp) { Dir.mktmpdir }

  it 'runs the package method' do
    described_class.new(:package, [:dist]) do |t, args|
      t.package = tmp
      t.dist = args
      t.version = '0.0.1'
      expect(args[:dist]).to eq('el8')
    end
    package = OodPackaging::Package.new(package: tmp, dist: 'el8', version: '0.0.1')
    allow(OodPackaging::Package).to receive(:new).and_return(package)
    expect(package).to receive(:run!)
    Rake.application.invoke_task('package[el8]')
  end
end
