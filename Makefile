
SHELL := /bin/bash


.PHONY:  tests create-env delete-env


tests:
	source ./.activate.sh; python -m pytest -v --cov=pyshapes tests/

create-env:
	bash ./.create-env-miniconda.sh

delete-env:
	rm -rf .env
	rm -f .activate.sh
