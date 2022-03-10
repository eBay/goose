venv:
	python3 -m venv venv
	venv/bin/pip3 install -r requirements.dev.txt

typecheck: venv
	venv/bin/mypy -m goose.web_service

tests: venv
	make typecheck
	venv/bin/pytest
	black --check goose

reformat: venv
	black goose/

watch:
	watchexec --ignore '.#.*' -e py make tests

web: venv
	venv/bin/hypercorn --bind 0.0.0.0:5000 --debug goose.web_service:app
