.PHONY: validate test clean help install

help:
	@echo "Available commands:"
	@echo "  make install   - Install dependencies"
	@echo "  make validate  - Run schema validation script"
	@echo "  make test      - Run pytest test suite"
	@echo "  make clean     - Clean generated reports"
	@echo "  make all       - Run validate and test"

install:
	pip install pandas pyyaml numpy pytest

validate:
	python src/validate_schema.py

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
