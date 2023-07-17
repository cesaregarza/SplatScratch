import base64
import datetime as dt
import glob
import json
import pathlib

import pandas as pd
import sqlalchemy as db
from sqlalchemy.sql.sqltypes import TypeEngine
from tqdm import tqdm

from parsing.splatoon3_ink.schedules import build_x_schedule_reference

PATTERN = "data/splatoon3_ink/*/*/*/xrank/*.json"


def base64_decode(x: str) -> str:
    try:
        return base64.b64decode(x).decode("utf-8")
    except TypeError:
        return None


def get_paths(
    latest_date: dt.datetime = dt.datetime(2022, 12, 31)
) -> list[str]:
    """Get all paths to json files in splatoon3.ink data

    Args:
        latest_date (dt.datetime): Get all paths after this date

    Returns:
        list[str]: List of paths to json files
    """
    paths = glob.glob(PATTERN)
    paths = [
        parse_path(path)
        for path in paths
        if "weapons" not in path and "detail" in path
    ]
    paths = [path for path in paths if path[0] >= latest_date]
    # Sort by datetime
    paths = sorted(paths, key=lambda x: x[0])
    return paths


def parse_path(path: str) -> tuple[dt.datetime, str, str]:
    filename = pathlib.Path(path).name
    parts = filename.split(".")
    date, time, _, _, region, rule, _ = parts
    datetime = dt.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H-%M-%S")
    return datetime, region, rule, path


def read_path(path: str) -> list[dict]:
    """Parallelizable function to get data from a path

    Args:
        path (str): Path to json file

    Returns:
        pd.DataFrame: Dataframe of json file
    """
    with open(path, "r") as f:
        data = json.load(f)
    node: dict = data["data"]["node"]
    key = [key for key in node.keys() if "xRanking" in key][0]
    return node[key]["edges"]


def parse_dict(
    data: dict, datetime: dt.datetime, region: str, rule: str
) -> pd.DataFrame:
    """Parse a dictionary from splatoon3.ink

    Args:
        data (dict): Dictionary from splatoon3.ink
        datetime (dt.datetime): Datetime of data
        region (str): Region of data
        rule (str): Rule of data

    Returns:
        pd.DataFrame: Dataframe of parsed data
    """
    df = pd.json_normalize(data)
    df["datetime"] = datetime
    df["region"] = region
    df["rule"] = rule
    return df


def generate_base_dataframe(paths: list[str]) -> pd.DataFrame:
    dfs = []
    # Parallelize this
    for datetime, region, rule, path in tqdm(paths, desc="Paths"):
        try:
            data = read_path(path)
        except (json.decoder.JSONDecodeError, KeyError):
            continue
        df = parse_dict(data, datetime, region, rule)
        keep_cols = [
            "node.id",
            "node.name",
            "node.rank",
            "node.rankDiff",
            "node.xPower",
            "node.weapon.name",
            "node.weapon.subWeapon.name",
            "node.weapon.specialWeapon.name",
            "node.weaponTop",
            "node.nameId",
            "node.nameplate.badges",
            "node.byname",
            "datetime",
            "region",
            "rule",
        ]
        rename_cols = [
            "node_id",
            "name",
            "rank",
            "rank_diff",
            "x_power",
            "weapon_name",
            "sub_weapon_name",
            "special_weapon_name",
            "weapon_top",
            "name_id",
            "nameplate_badges",
            "byname",
            "datetime",
            "region",
            "rule",
        ]
        try:
            df = df.loc[:, keep_cols]
        except KeyError:
            continue
        df.columns = rename_cols
        # Split nameplate badges
        for i in range(3):
            df[f"nameplate_badge_{i}"] = (
                df["nameplate_badges"]
                .str[i]
                .str["id"]
                .apply(base64_decode)
                .fillna("Badge-")
                .str[len("Badge-") :]
            )
        df = df.drop(columns=["nameplate_badges"])
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)

    return df


def append_schedule_data(
    x_df: pd.DataFrame, schedule_df: pd.DataFrame
) -> pd.DataFrame:
    schedule_col = (
        x_df["datetime"]
        .sub(dt.timedelta(hours=1))
        .dt.floor("2H")
        .dt.tz_localize("UTC")
    )
    for col in ["rule", "stage_1", "stage_2"]:
        x_df[f"schedule_{col}"] = schedule_col.map(schedule_df[col])
    return x_df


def generate_dataframe(
    paths: list[str],
    schedule_df: pd.DataFrame,
    conn_engine: db.engine.Engine,
    batch_size: int = 5_000,
    dtypes: dict[str, TypeEngine] | None = None,
) -> pd.DataFrame:
    partitions = [
        paths[i : i + batch_size] for i in range(0, len(paths), batch_size)
    ]

    for partition in tqdm(partitions, desc="Partitions"):
        df = generate_base_dataframe(partition)
        df = append_schedule_data(df, schedule_df)
        df.to_sql(
            "x_ranking",
            conn_engine,
            if_exists="append",
            index=False,
            dtype=dtypes,
        )
        del df

    return None


def generate_paths(
    conn_engine: db.engine.Engine | None = None,
) -> list[str]:
    # Get latest date from database
    if conn_engine is None:
        return get_paths()

    latest_date = pd.read_sql(
        "SELECT MAX(datetime) AS ldt FROM x_ranking", conn_engine
    )
    latest_date = latest_date["ldt"].pipe(pd.to_datetime).iloc[0]
    return get_paths(latest_date=latest_date)
