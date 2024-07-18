#!/usr/bin/env python
# coding: utf-8

import os
import sys
import uuid
import pickle

import boto3
import pandas as pd
from prefect import flow, task
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder

pd.options.mode.chained_assignment = None

data_path_env_key = "TRAIN_DATA_PATH"
model_dest_env_key = "MODEL_DEST_PATH"
aws_endpoint_url = os.getenv("AWS_ENDPOINT_URL", os.getenv("AWS_ENDPOINT_URL_S3"))


def get_storage_type(path: str):
    if path.startswith("s3://"):
        return "s3"
    return "local"


def get_data_type(path: str):
    if path.replace(".gz", "").endswith(".parquet"):
        return "parquet"
    if path.replace(".gz", "").endswith(".csv"):
        return "csv"
    if path.replace(".gz", "").endswith(".pickle"):
        return "pickle"
    return "unknown"


def get_storage_options(storage_type):
    if storage_type == "s3" and aws_endpoint_url:
        return {'client_kwargs': {'endpoint_url': aws_endpoint_url}}
    return {}


def drop_outliers(df):
    """
    The dataset uses 13-level age category: 1 = 18-24; 9 = 60-64; 13 = 80 or older.
    Let's say, we're not interested in the 13th category so let's drop outliers
    """
    print("Drop outliers")
    return df[(df["Age"] >= 1) & (df["Age"] <= 12)]


def create_ids(df):
    """
    Add UUID to each element of the dataframe
    """
    print("Create IDs")
    df['uuid'] = df.apply(lambda _: uuid.uuid4(), axis=1)


@task(name="Read data", log_prints=True)
def read_data(data_src):
    """
    Read 'csv' or 'parquet' data from two sources - local FS or S3
    """
    print(f"Read data from {data_src}")
    storage_type = get_storage_type(data_src)
    if get_data_type(data_src) == "csv":
        return pd.read_csv(data_src, storage_options=get_storage_options(storage_type))
    elif get_data_type(data_src) == "parquet":
        return pd.read_parquet(data_src, storage_options=get_storage_options(storage_type))
    elif get_data_type(data_src) == "pickle":
        if get_storage_type(data_src) == "s3":
            s3_client = boto3.client("s3")
            try:
                bucket = data_src.split("/")[2]
                key = "/".join(data_src.split("/")[3:])
            except IndexError:
                print(f"Incorrect S3 path: {data_src}")
                return
            return pickle.load(s3_client.get_object(Bucket=bucket, Key=key)['Body'])
        else:
            with open(data_src, "rb") as f:
                return pickle.load(f)
    else:
        sys.exit(
            f"Unknown data type for the data source: {data_src}. Known data types are 'csv', 'parquet', and 'pickle'"
        )


@task(name="Save data", log_prints=True)
def save_data(data, data_dest):
    """
    The function implies that there's only two options for a destination - 's3' and 'local' (default)
    """
    print("Serializa data")
    serialized_data = pickle.dumps(data)
    print(f"Saving serialized data to {data_dest}")
    if get_storage_type(data_dest) == "s3":
        s3_client = boto3.client("s3")
        try:
            bucket = data_dest.split("/")[2]
            key = "/".join(data_dest.split("/")[3:])
        except IndexError:
            print(f"Incorrect S3 path: {data_dest}")
            return
        s3_client.put_object(Body=serialized_data, Bucket=bucket, Key=key)
    else:
        if os.sep in data_dest:
            os.makedirs(os.path.dirname(data_dest), exist_ok=True)
        with open(data_dest, "wb") as f:
            f.write(serialized_data)


@task(name="Prepare data", log_prints=True)
def prepare_data(df):
    df = drop_outliers(df)
    create_ids(df)
    return df


@task(name="Label encoding")
def label_encoding(df, target):
    x_matrix = df[df.columns.drop(target)].copy()
    label_encoder = LabelEncoder()
    for column in x_matrix:
        x_matrix[column] = label_encoder.fit_transform(df[column])
    return x_matrix, label_encoder


@task(name="Train model")
def train_model(x_matrix, y_vector):
    return LinearRegression().fit(x_matrix, y_vector)


@flow(name="Diabetes prediction model training")
def model_pipeline(data_path, save_path):
    # Assume that we always try to predict only these values
    target = "Diabetes_012"
    df = read_data(data_path)
    df = prepare_data(df)
    x_matrix, encoder = label_encoding(df, target)
    y_vector = df[target]
    model = train_model(x_matrix, y_vector)
    save_data((model, encoder), save_path)


if __name__ == "__main__":
    try:
        data_path = sys.argv[1]
        save_path = sys.argv[2]
    except IndexError:
        try:
            data_path = os.getenv(data_path_env_key)
            save_path = os.getenv(model_dest_env_key)
        except KeyError:
            sys.exit(
                f"""Provide train data and model destination paths as arguments or as
                '{data_path_env_key}' and '{model_dest_env_key}' env vars"""
            )
    model_pipeline(data_path, save_path)
