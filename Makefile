



delete-virtualenv:
	rm -rf .env
	rm .activate.sh

freeze:
	pip freeze > requirements.txt
