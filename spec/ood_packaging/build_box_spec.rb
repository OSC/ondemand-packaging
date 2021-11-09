# frozen_string_literal: true

require 'spec_helper'

describe OodPackaging::BuildBox do
  let(:dist) { 'el8' }
  let(:build_box) { described_class.new(dist: dist) }

  before do
    allow(build_box).to receive(:podman_runtime?).and_return(false)
    allow(build_box).to receive(:build_dir).and_return('/fake-builddir')
    allow(build_box).to receive(:dockerfile).and_return('/tmp/dockerfile')
  end

  describe 'invalid' do
    it 'does not allow invalid dist' do
      expect { described_class.new(dist: 'foobar') }.to raise_error(ArgumentError)
    end
  end

  describe 'build_cmd' do
    before do
      allow(build_box).to receive(:build_gem)
    end

    context 'when building for el7' do
      let(:dist) { 'el7' }

      it 'executes el7 build command' do
        expected_cmd = [
          'docker build',
          "--tag ohiosupercomputer/ood-buildbox-el7:#{OodPackaging::VERSION}",
          '-f /tmp/dockerfile /fake-builddir'
        ]
        expect(build_box).to receive(:sh).with(expected_cmd.join(' '))
        build_box.build!
      end
    end

    context 'when building for el8' do
      it 'executes el8 build command' do
        expected_cmd = [
          'docker build',
          "--tag ohiosupercomputer/ood-buildbox-el8:#{OodPackaging::VERSION}",
          '-f /tmp/dockerfile /fake-builddir'
        ]
        expect(build_box).to receive(:sh).with(expected_cmd.join(' '))
        build_box.build!
      end
    end

    context 'when building for ubuntu-20.04' do
      let(:dist) { 'ubuntu-20.04' }

      it 'executes ubuntu-20.04 build command' do
        expected_cmd = [
          'docker build',
          "--tag ohiosupercomputer/ood-buildbox-ubuntu-20.04:#{OodPackaging::VERSION}",
          '-f /tmp/dockerfile /fake-builddir'
        ]
        expect(build_box).to receive(:sh).with(expected_cmd.join(' '))
        build_box.build!
      end
    end
  end

  describe 'push' do
    it 'executeses push image command' do
      expect(build_box).to receive(:sh).with("docker push ohiosupercomputer/ood-buildbox-el8:#{OodPackaging::VERSION}")
      build_box.push!
    end
  end
end
