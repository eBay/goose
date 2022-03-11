executable_prefix := ./venv/bin/

venv:
	@echo "running!"
ifeq ($(global_install),)
	python3 -m venv venv
	venv/bin/pip3 install -r requirements.dev.txt
else
	@echo "It's a global install"
	touch venv
executable_prefix =
endif

typecheck: venv
	${executable_prefix}mypy -m goose.web_service

tests: venv
	${executable_prefix}pytest

validate: venv
	make typecheck tests lint
	${executable_prefix}black --check goose

reformat: venv
	${executable_prefix}black goose/

lint: venv
	${executable_prefix}pylint goose/ || ${executable_prefix}pylint-exit -efail $$?

watch:
	watchexec --ignore '.#.*' -e py make tests

web: venv
	venv/bin/hypercorn --bind 0.0.0.0:5000 --debug goose.web_service:app
