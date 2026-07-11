.PHONY: test test-unit lint typecheck

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

lint:
	ruff check harness/ tests/

typecheck:
	mypy harness/