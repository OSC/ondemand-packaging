# frozen_string_literal: true

require 'spec_helper'

describe OodPackaging do
  it 'gets package version for dist el8' do
    expect(described_class.package_version('ondemand-release-latest', 'el8')).to eq('1-8')
  end

  it 'gets package version for dist ubuntu-20.04' do
    expect(described_class.package_version('ondemand-release-latest', 'ubuntu-20.04')).to eq('1')
  end
end
