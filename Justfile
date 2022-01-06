default_test_suite := 'tests/unittests'

test: unittest lint

lf:
    poetry run pytest -sxvvv --lf

unittest test_suite=default_test_suite:
    poetry run pytest -sxv {{test_suite}}

lint:
    poetry run flake8

black:
    poetry run isort .
    poetry run black .

cov test_suite=default_test_suite:
    rm -f .coverage
    rm -rf htmlcov
    poetry run pytest --cov-report=html --cov=blacksmith {{test_suite}}
    xdg-open htmlcov/index.html
