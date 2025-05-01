# -*- coding: utf-8 -*-
from pandas import DataFrame
import pandas as pd
import numpy as np


def map_normalized_titles(normalized_titles, excel_data: list):
    """maps title of excel to
    normmalized titles in db
    and assign normalized ids.

    Args:
        normalized_titles: array of normalized titles ORM object
        excel_data: excel data Dataframe uploaded by user

    Returns:
        dataframe with title name, and normalized ids
    """

    normalized_title_dict = {
        item.id: {
            key: value
            for key, value in item.__dict__.items()
            if key != "_sa_instance_state"
        }
        for item in normalized_titles
    }

    normalized_titles_df = DataFrame.from_dict(
        normalized_title_dict, orient="index"
    ).reset_index()

    data = excel_data.copy()
    data_titles = DataFrame(data, columns=["title"])

    new_df = pd.merge(
        data_titles,
        normalized_titles_df,
        left_on="title",
        right_on="name",
        how="left",
    )
    new_df = new_df.drop(["name"], axis=1)
    new_df.rename(columns={"id": "normalized_title_id", "title": "name"}, inplace=True)
    new_df["normalized_title_id"] = new_df["normalized_title_id"].replace(np.nan, None)

    return new_df[["name", "normalized_title_id"]]
