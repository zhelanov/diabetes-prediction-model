#!/usr/bin/env python
# coding: utf-8

import os
import sys
import uuid
import pickle
from datetime import datetime

import mlflow
import pandas as pd
from prefect import flow, task
from sklearn.metrics import root_mean_squared_error

from diabetes_prediction_model import read_data, save_data, prepare_data, label_encoding

data_path_env_key = "DATA_PATH"
model_dest_env_key = "MODEL_PATH"
mlflow_tracking_server = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
mlflow_experiment = os.getenv("MLFLOW_EXPERIMENT", "diabetes-prediction")


def setup_mlflow():
    print("Setup MLFlow")
    try:
        mlflow.set_tracking_uri(mlflow_tracking_server)
    except ConnectionRefusedError:
        sys.exit(f"Can't connect to the MLFlow tracking server: {mlflow_tracking_server}")
    mlflow.set_experiment(mlflow_experiment)
    mlflow.sklearn.autolog()


@task(name="Prepare validation dataframe")
def prepare_validation_dataframe(data_path):
    target = "Diabetes_012"
    df = read_data(data_path)
    df = prepare_data(df)
    x_matrix, _ = label_encoding(df, target)
    y_vector = df[target]
    return df, x_matrix, y_vector


@task(name="Get model", log_prints=True)
def get_model(model_path):
    model, _ = read_data(model_path)
    if model_path.startswith("s3://"):
        print("Downloaded the model from S3. Save locally to provide as an artifact to MLFlow later")
        tmp = f"mlruns/model-{uuid.uuid4()}"
        print(f"Save the model to '{tmp}'")
        with open(tmp, "wb") as f:
            pickle.dump(model, f)
    return model, tmp


@task(name="Get prediction")
def get_prediction(model, x_matrix):
    return model.predict(x_matrix)


@flow(name="Validate model")
def validate_model(data_path, model_path, register_model, remote_artifact_path="models"):
    with mlflow.start_run() as run:
        df, x_matrix, y_vector = prepare_validation_dataframe(data_path)
        model, local_artifact_path = get_model(model_path)
        prediction_df = pd.DataFrame()
        prediction_df['uuid'] = df['uuid']
        prediction_result = get_prediction(model, x_matrix)
        prediction_df['prediction'] = prediction_result
        save_data(prediction_df, f"output/prediction-{datetime.now().strftime('%y%m%d-%H%M%S')}")

        rmse = root_mean_squared_error(y_vector, prediction_result)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("intercept", model.intercept_)
        mlflow.log_artifact(local_path=local_artifact_path, artifact_path=remote_artifact_path)
        mlflow.sklearn.log_model(model, artifact_path=remote_artifact_path)
        if register_model:
            # Let's assume that we register only models which pass this criteria
            if rmse < 1:
                mlflow.register_model(
                    model_uri=f"runs:/{run.info.run_id}/{remote_artifact_path}",
                    name="Diabetes model",
                    tags={"type": "extremely dummy"},
                )
            else:
                sys.exit(f"The model provided invalid RMSE output: {rmse}")


if __name__ == "__main__":
    try:
        data_path = sys.argv[1]
        model_path = sys.argv[2]
        register_model = bool(sys.argv[3]) if len(sys.argv) == 4 else False
    except IndexError:
        try:
            data_path = os.getenv(data_path_env_key)
            model_path = os.getenv(model_dest_env_key)
        except KeyError:
            sys.exit(
                f"Provide train data and model destination paths as arguments or as '{data_path_env_key}' and '{model_dest_env_key}' env vars"
            )
    setup_mlflow()
    validate_model(data_path, model_path, register_model)
