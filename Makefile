venv:
	python3 -m venv venv
	venv/bin/pip3 install -r requirements.dev.txt

install: venv
	venv/bin/pip3 install -r requirements.txt

tests: venv
	venv/bin/pytest -v --cov=. --cov-branch --cov-report=term-missing --cov-fail-under=100 --durations=0 .
	venv/bin/mypy henrybot/*.py

watch:
	watchexec --ignore '.#.*' -e py make tests

web: venv
	venv/bin/hypercorn --bind 0.0.0.0:5000 --debug henrybot.web_service:app
