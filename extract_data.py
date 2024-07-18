#!/usr/bin/env python
# coding: utf-8
import pandas as pd

if __name__ == "__main__":
    # The data provided in float64 but actually contains only integer values
    df = pd.read_csv("data/diabetes_012_health_indicators_BRFSS2015.csv").astype("int")
    df_train = df[:150000]
    df_valid = df[100000:]
    # pandas parquet to GZip does not GZip the parquet, but makes an internally GZipped parquet,
    # the header of the file has the Parquet magic bytes (not the GZ ones!)
    df_train.to_parquet("data/diabetes_int_train.parquet", compression='gzip')
    df_valid.to_parquet("data/diabetes_int_valid.parquet", compression='gzip')
