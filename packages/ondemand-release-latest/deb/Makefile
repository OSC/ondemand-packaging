DIR := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))

.PHONY: tar
TAR := tar
VERSION := 1

tar:
	mkdir -p $(DIR)/build
	cd $(DIR) ; git ls-files . | $(TAR) -c \
		--transform 's,^,ondemand-release-latest-$(VERSION)/,' -T - | gzip > $(DIR)/build/ondemand-release-latest-$(VERSION).tar.gz
