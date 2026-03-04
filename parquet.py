import os
import pandas as pd
from pathlib import Path
import ast

def parquet_to_csv(in_path: Path, out_path: Path, **kwargs):
    """Parquet → CSV"""
    df = pd.read_parquet(in_path, engine="pyarrow")
    df.to_csv(out_path, index=False, **kwargs)
    print(f"✔ Saved CSV → {out_path}")

def csv_to_parquet(in_path: Path, out_path: Path, **kwargs):
    """CSV → Parquet"""
    df = pd.read_csv(in_path, **kwargs)
    # 將 observation.state 轉成字串
    df.to_parquet(out_path, engine="pyarrow", index=False)
    print(f"✔ Saved Parquet → {out_path}")

def string_to_float(filename):
    # 讀取 Parquet
    df = pd.read_parquet(filename)

    # 將字串轉成 list[float]
    df["observation.state"] = df["observation.state"].apply(lambda x: [float(i) for i in ast.literal_eval(x)])
    df["action"] = df["action"].apply(lambda x: [float(i) for i in ast.literal_eval(x)])

    # 寫入新的 Parquet，保持 list[float64] 結構
    df.to_parquet(filename, index=False)

if __name__ == "__main__":
    # main()
    # parquet_to_csv('episode_000001.parquet', './episode_000001.csv')
    # for i in range(0, 10):
    #     parquet_to_csv(
    #         f'task_0/data/chunk-000/episode_{i:06d}.parquet',
    #         f'task_0/data/chunk-000/episode_{i:06d}.csv'
    #     )
    # csv_to_parquet('output.csv','output.parquet')
    csv_path = os.path.join(f'task_0', 'data', 'chunk-000', 'episode_000000.csv')
    parquet_path = os.path.join(f'task_0', 'data', 'chunk-000', 'episode_000000.parquet')
    csv_to_parquet(csv_path, parquet_path)
    # string_to_float('task_1\data\chunk-000\episode_000000.parquet')
    