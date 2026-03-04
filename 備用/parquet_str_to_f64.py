import pandas as pd
import ast

# 載入原始 parquet 檔案
df = pd.read_parquet('task_0/data/chunk-000/episode_000000.parquet')

# 嘗試將字串轉成 list[float]
def safe_str_to_float_list(val):
    try:
        # 如果已經是 list，就跳過
        if isinstance(val, list):
            return val
        # 嘗試轉為 list 並轉為 float
        return [float(i) for i in ast.literal_eval(val)]
    except (ValueError, SyntaxError, TypeError):
        return None  # 有錯就回傳 None，避免影響轉存

# 轉換 observation.state 和 action
df["observation.state"] = df["observation.state"].apply(safe_str_to_float_list)
df["action"] = df["action"].apply(safe_str_to_float_list)

# 最後確保每個值要嘛是 list 要嘛是 None
def ensure_list_or_none(val):
    return val if isinstance(val, list) or pd.isna(val) else None

df["observation.state"] = df["observation.state"].apply(ensure_list_or_none)
df["action"] = df["action"].apply(ensure_list_or_none)

# 儲存為新的 parquet
df.to_parquet('task_0/data/chunk-000/episode_000000.parquet', engine="pyarrow", index=False)

print("✅ 轉換與儲存完成")
