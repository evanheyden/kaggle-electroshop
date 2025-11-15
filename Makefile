# Validate any dataset via DATA=... override
PYTHON ?= python3
CONTRACT ?= configs/data_contract.yaml
REPORTS_DIR ?= reports

RAW_DATA ?= data/raw/dsba-m-1-challenge-purchase-prediction/train_dataset_M1_with_id.csv
INTERIM_DATA ?= data/interim/train_dataset_M1_interim.csv

.PHONY: validate test clean help install preprocess

help:
	@echo "Available commands:"
	@echo "  make install   - Install dependencies"
	@echo "  make preprocess - Run preprocessing pipeline"
	@echo "  make test      - Run pytest test suite"
	@echo "  make clean     - Clean generated reports"
	@echo "  make all       - Run validate and test"
	@echo "	 make validate DATA=path/to.csv [CONTRACT=path/to.yaml] [REPORTS_DIR=dir]"
	@echo "	 make validate-raw"
	@echo "	 make validate-interim"

install:
	pip install pandas pyyaml numpy pytest

preprocess:
	$(PYTHON) src/preprocess.py

validate:
	$(PYTHON) -m src.validate_schema --data "$(DATA)" --contract "$(CONTRACT)" --reports-dir "$(REPORTS_DIR)"

validate-raw:
	$(PYTHON) -m src.validate_schema --data "$(RAW_DATA)" --contract "$(CONTRACT)" --reports-dir "$(REPORTS_DIR)" --tag raw

validate-interim:
	$(PYTHON) -m src.validate_schema --data "$(INTERIM_DATA)" --contract "$(CONTRACT)" --reports-dir "$(REPORTS_DIR)" --tag interim

test:
	pytest src/tests/test_schema.py -v

test-quiet:
	pytest src/tests/test_schema.py -q

clean:
	rm -f reports/schema_key_violations.csv
	rm -f reports/nulls_overview.csv
	rm -rf .pytest_cache
	rm -rf src/tests/__pycache__
	rm -rf src/__pycache__

all: validate test
