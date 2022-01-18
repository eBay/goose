install:
	python3 -m venv .venv
	.venv/bin/pip3 install -r requirements.txt

tests:
	pytest -v --cov=. --cov-branch --cov-report=term-missing --cov-fail-under=100 --durations=0 .

web:
	python web_service.py
