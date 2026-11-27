# frozen_string_literal: true

require 'spec_helper'

describe OodPackaging do
  it 'gets package version for dist el9' do
    expect(described_class.package_version('ondemand-release', 'el10')).to eq('4.3')
  end

  it 'gets package version for dist ubuntu-26.04' do
    expect(described_class.package_version('ondemand-release', 'ubuntu-26.04')).to eq('4.3.0')
  end
end
