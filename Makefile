LOCAL_TAG:=$(shell date +"%Y-%m-%d-%H-%M")
LOCAL_IMAGE_NAME:=stream-model-duration:${LOCAL_TAG}

test:
	poetry run pytest tests/

quality_checks:
	poetry run isort .
	poetry run black .
	poetry run pylint --recursive=y .

build: quality_checks test
	docker build -t ${LOCAL_IMAGE_NAME} .

integration_test: build
	LOCAL_IMAGE_NAME=${LOCAL_IMAGE_NAME} bash integration-tests/run.sh

setup:
	pip3 install --user poetry
	poetry install
	poetry run pre-commit install
