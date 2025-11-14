# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python (fantasy)
#     language: python
#     name: fantasy
# ---

# %% [markdown]
# # NFL Fantasy dev

# %% [markdown]
#
#

# %%
import nflreadpy as nfl

# Load current season play-by-play data
pbp = nfl.load_pbp()


# %%
pbp.shape

# %%
player_stats = nfl.load_player_stats([2022, 2023, 2024, 2025])
player_stats.head()

# %%
import polars as pl

MC_stats = player_stats.filter(pl.col("player_display_name") == "Christian McCaffrey")


# %%
MC_stats

# %%
MC_stats_clean = MC_stats.select(
    [col_name for col_name in MC_stats.columns if not MC_stats[col_name].is_null().all()]
)


# %%
MC_stats_clean

# %%
MC_stats_clean_final = MC_stats_clean.select(
    [col_name for col_name in MC_stats_clean.columns if MC_stats_clean[col_name].mean() != 0]
)

# %%
MC_stats_clean_final

# %%
# !pip install matplotlib

# %%
import matplotlib.pyplot as plt

# --- 3. Convertir season y week a enteros y crear columna "season_week" ---
df = MC_stats_clean_final.with_columns(
    [
        pl.col("season").cast(pl.Int32),
        pl.col("week").cast(pl.Int32),
        (pl.col("season").cast(pl.Utf8) + "-W" + pl.col("week").cast(pl.Utf8)).alias("season_week"),
    ]
)

# --- 4. Ordenar cronológicamente ---
df = df.sort(["season", "week"])

# --- 5. Convertir a pandas para graficar ---
df_pd = df.to_pandas()

# --- 6. Graficar ---
plt.figure(figsize=(12, 6))
plt.plot(df_pd["season_week"], df_pd["rushing_yards"], marker="o", linestyle="-")
plt.title("Rushing Yards Over Time")
plt.xlabel("Season - Week")
plt.ylabel("Rushing Yards")
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# %%
