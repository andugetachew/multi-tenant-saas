# Makefile
.PHONY: test test-cov test-accounts test-projects test-all

test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term

test-accounts:
	pytest accounts/tests/ -v

test-projects:
	pytest projects/tests/ -v

test-organizations:
	pytest organizations/tests/ -v

test-all:
	pytest -v --tb=short

test-watch:
	ptw --runner "pytest"