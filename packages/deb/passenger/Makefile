DIR := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))

.PHONY: tar
TAR := tar
VERSION := 6.0.11

tar:
	cd $(DIR) ; git ls-files . | $(TAR) -c \
		--transform 's,^,passenger-$(VERSION)/,' -T - | gzip > $(DIR)/build/passenger-$(VERSION).tar.gz
