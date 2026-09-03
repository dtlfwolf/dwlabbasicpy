SHELL := /bin/bash

ROOT := $(abspath $(CURDIR))
DWLAB_ARTIFACTS_ROOT ?= $(abspath $(ROOT)/../dwlab-packages)
PACKAGES_DIR ?= $(DWLAB_ARTIFACTS_ROOT)
PACKAGE_NAME := dwlabbasicpy
PYTHON ?= python3
BUILD_ARTIFACTS ?= $(ROOT)/dist
WHEEL_OUTPUT_DIR ?= $(BUILD_ARTIFACTS)/wheels
PACKAGE_VERSION := $(shell awk -F'"' '/^version = / { print $$2; exit }' pyproject.toml)
WHEEL_FILE := $(WHEEL_OUTPUT_DIR)/$(PACKAGE_NAME)-$(PACKAGE_VERSION)-py3-none-any.whl
WHEEL_MANIFEST := $(WHEEL_OUTPUT_DIR)/$(PACKAGE_NAME)-$(PACKAGE_VERSION).sha256
INSTALL_TARGET ?=

.PHONY: help build wheel rebuild-wheel clean-wheel clean inspect install

help:
	@echo "Targets for $(PACKAGE_NAME):"
	@echo "  make build        Build wheel and sdist artifacts into $(BUILD_ARTIFACTS)"
	@echo "  make wheel        Build one reusable wheel and checksum into WHEEL_OUTPUT_DIR"
	@echo "  make rebuild-wheel Remove and rebuild only WHEEL_OUTPUT_DIR"
	@echo "  make clean        Remove local build artifacts"
	@echo "  make inspect      List generated distribution files"
	@echo "  make install      Pip install into INSTALL_TARGET or the active environment"

build:
	$(PYTHON) -m build --no-isolation --outdir "$(BUILD_ARTIFACTS)"

wheel:
	@mkdir -p "$(WHEEL_OUTPUT_DIR)"
	$(PYTHON) -m build --wheel --no-isolation --outdir "$(WHEEL_OUTPUT_DIR)"
	@test -f "$(WHEEL_FILE)" || (echo "Expected wheel not produced: $(WHEEL_FILE)"; exit 2)
	@sha256sum "$(WHEEL_FILE)" > "$(WHEEL_MANIFEST)"
	@echo "Built verified wheel: $(WHEEL_FILE)"

rebuild-wheel:
	$(MAKE) clean-wheel WHEEL_OUTPUT_DIR="$(WHEEL_OUTPUT_DIR)"
	$(MAKE) wheel WHEEL_OUTPUT_DIR="$(WHEEL_OUTPUT_DIR)"

clean-wheel:
	rm -rf "$(WHEEL_OUTPUT_DIR)"

clean:
	rm -rf .pybuild build "$(BUILD_ARTIFACTS)" *.egg-info src/*.egg-info

inspect:
	@ls -1 "$(BUILD_ARTIFACTS)"/$(PACKAGE_NAME)-* 2>/dev/null || echo "No distribution artifacts built yet."

install:
	$(PYTHON) -m pip install $(if $(INSTALL_TARGET),--target "$(INSTALL_TARGET)",.) .
