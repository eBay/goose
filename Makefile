tests:
	pytest --cov=. --cov-branch --cov-report=term-missing --cov-fail-under 100 .
