import glob
import json

import pandas as pd
import tqdm


def read_schedule(path: str, mode: str, offset: int = 0) -> dict:
    """Reads a schedule file into a dict

    Args:
        path (str): Path to the schedule file
        mode (str): The mode to parse. "regularSchedules", "bankaraSchedules", "xSchedules" are valid
        offset (int, optional): The position of the schedule to read. Defaults to 0.

    Returns:
        dict: The schedule data
    """
    with open(path, "r") as f:
        data = json.load(f)
    return data["data"][mode]["nodes"][offset]


def build_x_schedule_reference():
    paths = glob.glob("data/splatoon3_ink/*/*/*/*.schedules.json")
    dfs = []
    for path in tqdm.tqdm(paths):
        try:
            data = read_schedule(path, "xSchedules")
        except (json.decoder.JSONDecodeError, KeyError):
            continue
        df = pd.json_normalize(data)
        dfs.append(df)
    df = pd.concat(dfs)
    return x_schedule_postprocessing(df)


def x_schedule_postprocessing(df: pd.DataFrame) -> pd.DataFrame:
    df["stage_1"] = df["xMatchSetting.vsStages"].str[0].str["name"]
    df["stage_2"] = df["xMatchSetting.vsStages"].str[1].str["name"]
    df["startTime"] = pd.to_datetime(df["startTime"])
    df["endTime"] = pd.to_datetime(df["endTime"])
    columns = [
        "startTime",
        "endTime",
        "xMatchSetting.vsRule.name",
        "stage_1",
        "stage_2",
    ]
    df = df.loc[:, columns].copy()
    df.columns = [
        "start_time",
        "end_time",
        "rule",
        "stage_1",
        "stage_2",
    ]
    df["rule"] = df["rule"].str.lower().str.replace("\s", "", regex=True)

    return (
        df.drop_duplicates()
        .set_index("start_time")
        .sort_index()
        .fillna("Splatfest")
    )
