.PHONY: install run test lint

install:
	python -m pip install -e ".[dev]"

run:
	streamlit run app.py

test:
	pytest --cov=dataguard --cov-report=term-missing

lint:
	ruff check .

