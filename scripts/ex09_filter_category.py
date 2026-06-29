# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas"]
# ///
"""例題9: 分類事項で絞り込む（cdCat02）。

労働力調査（統計表ID 0003005865「労働力人口比率，就業率及び完全失業率」）から、
「就業状態」分類（cat02）を使って、就業率と完全失業率を取り出す。
複数コードはカンマ区切りで一度に指定できる。

実行:
    set -a; source .env; set +a
    uv run scripts/ex09_filter_category.py
"""
import estat_api as e

SID = "0003005865"


def main() -> None:
    app_id = e.get_app_id()

    sdata = e.get_stats_data(
        app_id, SID,
        cdTab="02",          # 表章項目: 率(％)
        cdCat01="000",       # 産業: 全産業
        cdCat02="13,08",     # 就業状態: 13=就業, 08=完全失業者（カンマで複数）
        cdCat03="0",         # 性別: 総数
        cdTimeFrom="2024000101",  # 2024年1月以降（この表の時間軸は月次・階層なし）
    )
    df = e.stats_data_to_frame(sdata).sort_values("time_code")

    # cat02（就業状態）ごとに直近の値を表示
    for state, sub in df.groupby("cat02"):
        latest = sub.iloc[-1]
        print(f"{state}：直近 {latest['time']} = {latest['値']}{latest['単位']}（{len(sub)}か月分取得）")


if __name__ == "__main__":
    main()
