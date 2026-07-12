.PHONY: test test-unit test-mock lint typecheck demo build

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-mock:
	pytest tests/mock/ -v

lint:
	ruff check harness/ tests/

typecheck:
	mypy harness/

demo:
	python3 -m demo.run_demo

build:
	python3 -m build