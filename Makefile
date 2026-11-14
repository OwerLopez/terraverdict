.PHONY: install test test-stat lint golden report
install:
	pip install -e ".[dev]"
test:
	pytest
test-stat:
	pytest -m slow
lint:
	ruff check src tests && mypy src
golden:
	pytest tests/unit/test_golden_preliminar.py -v
report:
	tv trends --series tests/fixtures/preliminar_series.json --out expedientes/
