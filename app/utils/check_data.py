# -*- coding: utf-8 -*-
import pandas as pd
from pandas import DataFrame

# Remove latitude and longitude when data type changed
# to float in database
string_columns: list[str] = [
    "employee_id",
    "manager_id",
    "first_name",
    "last_name",
    "currency",
    "location",
    "employee_type",
    "race_ethnicity",
    "gender",
    "title",
    "bus_unit",
    "bus_func",
    "bus_subfunc",
    "role_type",
    "latitude",
    "longitude",
]
int_columns: list[str] = []
float_columns: list[str] = [
    "base_compensation",
    "bonus",
    "fringe_benefits",
    "fully_loaded_compensation",
    "years_of_service",
]
datetime_columns: list[str] = [
    "hire_date",
    "exit_date",
]


def check_data_types(df_data: DataFrame):
    """casts expected data type to the incoming data
    raises error in case unable to cast data type

    Args:
        df_data: dataframe uplaoded by user containing
        all the columns mapped to application columns.

    Returns:
        dataframe with validated column data types
    """
    # Extract columns from df that are in the expected data type list
    df_string_columns = [
        item for item in df_data.columns.values if item in string_columns
    ]
    df_float_columns = [
        item for item in df_data.columns.values if item in float_columns
    ]

    # Check if string type columns have strigs as values
    df_data = check_string_type_data(data=df_data, column_names=df_string_columns)

    df_data = check_float_data_type(
        data=df_data, primary_id="employee_id", column_names=df_float_columns
    )

    return df_data


def check_string_type_data(data: pd.DataFrame, column_names: list[str]):
    """Cast Object type columns to string type columns. Raises
    an exception in case unable to cast expected string type columns
     as strings"""
    try:
        data[column_names] = data[column_names].astype(pd.StringDtype())
    except Exception as e:
        raise ValueError(
            "There was an issue with data type casting of string columns" f"{e}"
        )
    return data


def check_float_data_type(data: pd.DataFrame, primary_id: str, column_names: list[str]):
    """Cast float type columns as float and raise an
    exception informing user number of rows that
    have non float values"""
    bad_df = DataFrame()
    problem_columns: list[str] = []
    try:
        data[column_names] = data[column_names].astype("float64")
    except Exception:
        for item in column_names:
            bad_data = data.loc[
                pd.to_numeric(data[item], errors="coerce").isnull(),  # type: ignore
            ]
            if len(bad_data.index) != 0:
                problem_columns.append(item)
            bad_df = pd.concat([bad_data, bad_df])

        raise ValueError(
            f"Non float/decimal values were detected in columns mapped to "
            f"{problem_columns}. Count of {primary_id}s with non float values : "
            f"{len(bad_df[primary_id].unique())}"
        )
    return data


def detect_missing_data(data: pd.DataFrame, column_mapping: list):
    """checks data columns for missing values in the mapped columns
    and raises a 400 incase missing values are found. Returns a dict
    of column names and number of missing values in each column"""

    data_columns = list(data.columns.values)
    columns_with_missing_data = {}

    column_mapping_dict = {
        item.mapped_column_name: item.original_column for item in column_mapping
    }

    for item in data_columns:
        item_series = pd.isnull(data[item])
        null_data = data[item_series]
        if null_data.shape[0] != 0:
            columns_with_missing_data[column_mapping_dict[item]] = null_data.shape[0]

    if len(columns_with_missing_data) != 0:
        raise ValueError(
            f"Following missing values detected in column mapping"
            f" done by user: {columns_with_missing_data}"
            f" It is recommended that user fill up the missing values"
            f" either input empty string '' or 0.00 (if missing values not available)"
            f" and reupload the organization."
        )

    return data


def check_benchmark_data_integrity(data: pd.DataFrame, normalized_titles: list):
    """Check for missing/null/zero values in
    benchmarking columns and raise an exception if
    anomolies found in the column"""

    benchmark_data_columns = ["fully_loaded_compensation", "title"]

    zero_fully_loaded_compensation = data.loc[
        data[benchmark_data_columns[0]].isin([0]),  # type: ignore
    ]
    if zero_fully_loaded_compensation.shape[0] != 0:
        raise ValueError(
            f"Since the organization has been marked as benchmark "
            f"there cannot be 0 values in {benchmark_data_columns[0]}. "
            f"Please consider not marking this organization as benchmark "
            f"or treat the missing values before uploading the census data."
        )

    if len(normalized_titles) != 0:
        normalized_titles_dict = {item.name: item.id for item in normalized_titles}
        data["normalized_title_id"] = data["title"].map(normalized_titles_dict)
        null_normalized_titles = data.loc[
            data["normalized_title_id"].isnull(),  # type: ignore
        ]
        if null_normalized_titles.shape[0] != 0:
            raise ValueError(
                "Since the organization has been marked as benchmark "
                "there cannot be non normalized titles as it impacts data  "
                "integrity of benchmark data. Please consider using Title Normalization"
                " Application and map the correct column to title in column mapping"
                " or dont save this organization as a benchmark org."
            )

    return data
