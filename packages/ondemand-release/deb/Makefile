DIR := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))

.PHONY: tar
TAR := tar
VERSION := 2.1.0

tar:
	mkdir -p $(DIR)/build
	cd $(DIR) ; git ls-files . | $(TAR) -c \
		--transform 's,^,ondemand-release-$(VERSION)/,' -T - | gzip > $(DIR)/build/ondemand-release-$(VERSION).tar.gz
