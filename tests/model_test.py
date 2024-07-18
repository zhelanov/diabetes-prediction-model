import pandas as pd

import diabetes_prediction_model as dpm

# I intentionally written only a few tests here


def test_storage_type():
    assert dpm.get_storage_type("s3://bucket/object") == "s3"
    assert dpm.get_storage_type("local/file") == "local"


def test_data_type():
    assert dpm.get_data_type("path/to/file.parquet.gz") == "parquet"
    assert dpm.get_data_type("path/to/file.csv") == "csv"
    assert dpm.get_data_type("path/to/file.pickle.gz") == "pickle"
    assert dpm.get_data_type("path/to/file") == "unknown"


def test_drop_outliers():
    values = [-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 100]
    df = pd.DataFrame({"Age": values})
    assert dpm.drop_outliers(df)["Age"].to_list() == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
