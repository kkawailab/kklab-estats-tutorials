# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas"]
# ///
"""例題8: 地域で絞り込む（lvArea と cdArea）。

人口推計（令和2年国勢調査基準, 統計表ID 0003448232「都道府県，男女別人口」）から、
都道府県別の総人口を取り出す。
lvArea=2 で都道府県だけに、cdArea で特定県だけに絞る方法を示す。

実行:
    set -a; source .env; set +a
    uv run scripts/ex08_filter_area.py
"""
import estat_api as e

SID = "0003448232"  # 人口推計 都道府県，男女別人口－総人口，日本人人口


def main() -> None:
    app_id = e.get_app_id()

    # (1) lvArea=2 → 都道府県だけ（全国を除く）。男女計・総人口の最新年。
    sd = e.get_stats_data(app_id, SID,
                          cdTab="001", cdCat01="000", cdCat02="001", lvArea="2")
    df = e.stats_data_to_frame(sd)
    latest = df["time_code"].max()
    df = df[df["time_code"] == latest]
    print(f"対象年: {df['time'].iloc[0]} ／ 都道府県数: {len(df)}")
    print("人口の多い上位5都道府県（単位：千人）：")
    print(df.sort_values("値", ascending=False)[["area", "値"]].head(5).to_string(index=False))

    # (2) cdArea で特定の都道府県だけ（愛知県=23000, 東京都=13000）
    sd2 = e.get_stats_data(app_id, SID,
                           cdTab="001", cdCat01="000", cdCat02="001",
                           cdArea="23000,13000")
    df2 = e.stats_data_to_frame(sd2)
    df2 = df2[df2["time_code"] == df2["time_code"].max()]
    print("\ncdArea で愛知県・東京都だけを取得（最新年）：")
    print(df2[["area", "値", "単位"]].to_string(index=False))


if __name__ == "__main__":
    main()
