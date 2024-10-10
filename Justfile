package := 'pyramid_blacksmith'
default_test_suite := 'tests/unittests'

install:
    poetry install --with dev

doc:
    cd docs && poetry run make html
    xdg-open docs/build/html/index.html

cleandoc:
    cd docs && poetry run make clean

test: lint mypy unittest

lf:
    poetry run pytest -sxvvv --lf

unittest test_suite=default_test_suite:
    poetry run pytest -sxv {{test_suite}}

lint:
    poetry run flake8

mypy:
    poetry run mypy src/

black:
    poetry run isort .
    poetry run black .

fmt: black

gh-pages:
    poetry export --dev -f requirements.txt -o docs/requirements.txt --without-hashes

cov test_suite=default_test_suite:
    rm -f .coverage
    rm -rf htmlcov
    poetry run pytest --cov-report=html --cov={{package}} {{test_suite}}
    xdg-open htmlcov/index.html
release major_minor_patch: test gh-pages && changelog
    poetry version {{major_minor_patch}}
    poetry install

changelog:
    poetry run python scripts/write_changelog.py
    cat CHANGELOG.rst >> CHANGELOG.rst.new
    rm CHANGELOG.rst
    mv CHANGELOG.rst.new CHANGELOG.rst
    $EDITOR CHANGELOG.rst

publish:
    git commit -am "Release $(poetry run python scripts/show_release.py)"
    poetry build
    poetry publish
    git push
    git tag "$(poetry run python scripts/show_release.py)"
    git push origin "$(poetry run python scripts/show_release.py)"
