# https://stackoverflow.com/a/11482430
class String
  def colorize(code)
    "\e[#{code}m#{self}\e[0m"
  end

  def red
    colorize(31)
  end

  def green
    colorize(32)
  end

  def blue
    colorize(34)
  end
end
