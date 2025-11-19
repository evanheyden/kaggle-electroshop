# Validate any dataset via DATA=... override
PYTHON ?= python3
CONTRACT ?= configs/data_contract.yaml
REPORTS_DIR ?= reports

# File paths
RAW_TRAIN ?= data/raw/dsba-m-1-challenge-purchase-prediction/train_dataset_M1_with_id.csv
RAW_TEST ?= data/raw/dsba-m-1-challenge-purchase-prediction/test_dataset_M1_with_id.csv
INTERIM_TRAIN ?= data/interim/train_dataset_M1_interim.csv
INTERIM_TEST ?= data/interim/test_dataset_M1_interim.csv

# For backwards compatibility
RAW_DATA ?= $(RAW_TRAIN)
INTERIM_DATA ?= $(INTERIM_TRAIN)

.PHONY: validate test clean help install preprocess preprocess-train preprocess-test

help:
	@echo "Available commands:"
	@echo "  make install            - Install dependencies"
	@echo "  make preprocess         - Run preprocessing on both train and test datasets"
	@echo "  make preprocess-train   - Run preprocessing on train dataset only"
	@echo "  make preprocess-test    - Run preprocessing on test dataset only"
	@echo "  make test               - Run pytest test suite on raw data"
	@echo "  make test-interim       - Run pytest test suite on interim data"
	@echo "  make clean              - Clean generated reports"
	@echo "  make all                - Validate interim and run tests on interim"
	@echo "  make validate DATA=path/to.csv [CONTRACT=path/to.yaml] [REPORTS_DIR=dir]"
	@echo "  make validate-raw       - Validate raw data"
	@echo "  make validate-interim   - Validate interim data"

install:
	pip install pandas pyyaml numpy pytest

preprocess-train:
	$(PYTHON) src/preprocess.py --input "$(RAW_TRAIN)" --output "$(INTERIM_TRAIN)" --name "Train Dataset"

preprocess-test:
	$(PYTHON) src/preprocess.py --input "$(RAW_TEST)" --output "$(INTERIM_TEST)" --name "Test Dataset"

preprocess: preprocess-train preprocess-test

validate:
	$(PYTHON) -m src.validate_schema --data "$(DATA)" --contract "$(CONTRACT)" --reports-dir "$(REPORTS_DIR)"

validate-raw:
	$(PYTHON) -m src.validate_schema --data "$(RAW_DATA)" --contract "$(CONTRACT)" --reports-dir "$(REPORTS_DIR)" --tag raw

validate-interim:
	$(PYTHON) -m src.validate_schema --data "$(INTERIM_DATA)" --contract "$(CONTRACT)" --reports-dir "$(REPORTS_DIR)" --tag interim

test:
	pytest src/tests/test_schema.py -v

test-interim:
	pytest src/tests/test_schema.py -v -k "interim"

test-quiet:
	pytest src/tests/test_schema.py -q

clean:
	rm -f reports/schema_key_violations.csv
	rm -f reports/nulls_overview.csv
	rm -rf .pytest_cache
	rm -rf src/tests/__pycache__
	rm -rf src/__pycache__

all: validate-interim test-interim
