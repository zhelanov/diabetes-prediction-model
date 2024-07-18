# Diabetes prediction model

This repository contains a project for building a diabetes prediction model using the Diabetes Health Indicators Dataset.
The primary objective of this project is to demonstrate a Machine Learning Operations (MLOps) pipeline, as part of the MLOps-Zoomcamp course.
The project leverages Poetry for Python dependency management and virtual environment handling. The project's config is defined in `pyproject.toml`

## Table of Contents

- [Diabetes prediction model](#diabetes-prediction-model)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
  - [Dataset](#dataset)
  - [Project Structure](#project-structure)
  - [Initial setup](#initial-setup)
  - [Quick start](#quick-start)
  - [Build docker image](#build-docker-image)
  - [Train a model](#train-a-model)
  - [Infrastructure creation](#infrastructure-creation)

## Project Overview

This project involves creating a model to predict the likelihood of diabetes based on various health indicators. The primary goals include:

- **Setting up a reproducible Python environment using Poetry:** Ensuring that all dependencies are managed consistently and that the development environment can be easily reproduced by others.
- **Implementing a dummy predictive model for the dataset:** The model is not suitable to solve the actual problem and wasn't implied to be efficient or rational in any way - it was made just as an example.
- **Demonstrating the use of MLOps principles in a practical project:** Applying best practices in MLOps, including version control, automated testing, and continuous integration/continuous deployment (CI/CD), to streamline the model development and deployment process.

I had no intention to get maximum points according to [Evaluation Criteria](https://github.com/DataTalksClub/mlops-zoomcamp/blob/main/07-project/README.md#evaluation-criteria) so, for example, monitoring entirely was skipped on purpose.

## Dataset

The dataset used in this project is the Diabetes Health Indicators Dataset, which can be found on [Kaggle](https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset). The dataset consists of various health indicators related to diabetes.
It was downloaded manually (requires authorization) and then simplified by converting floats to integers and separated to two parts using `extract_data.py`.

## Project Structure

```plaintext
.
├── data
│   └── diabetes_int_train.parquet       # Train Dataset file
│   └── diabetes_int_valid.parquet       # Validation Dataset file
├── diabetes_prediction_model.py         # Model implementation
├── extract_data.py                      # Data preprocessing script
├── run_experiment.py                    # A script to run experiment and conditionally register the model
├── infrastructure                       # Terragrunt definitions for AWS S3 bucket to (potentially) store the model
├── integration-tests                    # Integration tests for model
├── tests                                # Unit tests for model
├── docker-compose.yaml                  # Docker-compose config to setup infrastructure for integration tests
├── pyproject.toml                       # Project configuration file
├── .pre-commit-config.yaml              # pre-commit tool config
```

## Initial setup

If you have `make` installed, simply run

```bash
make setup
```

otherwise, run

```bash
pip3 install --user poetry
poetry install
poetry run pre-commit install
```

## Quick start

One the initial setup is finished, run

```bash
bash integration-tests/run.sh
```

## Build docker image

```bash
docker build -t diabetes_prediction_model:0.0.1 .
```

## Train a model

```bash
poetry run python diabetes_prediction_model.py [data_path] [model_path]
```

Examples:

```bash
poetry run python diabetes_prediction_model.py data/diabetes_int_train.parquet models/model.bin
poetry run python diabetes_prediction_model.py s3://mybucket/data/diabetes_int_train.parquet s3://mybucket/new-model.bin
```

Specify the required AWS-related environment variables if you work with S3.
If you work with localstack instead, specify these variables:

```bash
export AWS_ENDPOINT_URL="http://localhost:4566"
export AWS_REGION="us-west-2"
```

## Infrastructure creation

The required infrastructure (I declared only S3 as an example) is defined in `infrastructure` directory and the resources can be created using `terragrunt` (a wrapper over terraform):

```bash
terragrunt apply --terragrunt-working-dir s3/dev
```
