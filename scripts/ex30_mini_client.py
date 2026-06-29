# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas"]
# ///
"""例題30: 共通モジュールを使った「景気指標ダッシュボード」と英語メタの取得。

これまで作った estat_api モジュールを使って、複数の統計から最新値を集めて
一覧表示する総合例。最後に lang="E" を指定して英語のメタ情報を取得する方法も示す。

実行:
    set -a; source .env; set +a
    uv run scripts/ex30_mini_client.py
"""
import estat_api as e


def latest_value(app_id, sid, **cond) -> tuple[str, float, str]:
    """指定条件で取得した系列の最新値 (時点, 値, 単位) を返す。"""
    sdata = e.get_stats_data(app_id, sid, **cond)
    df = e.stats_data_to_frame(sdata).sort_values("time_code")
    row = df.iloc[-1]
    return row["time"], row["値"], row.get("単位", "")


def main() -> None:
    app_id = e.get_app_id()

    print("===== 主要経済指標ダッシュボード =====")
    indicators = [
        ("消費者物価指数 前年同月比（総合）", "0003427113",
         dict(cdTab="3", cdCat01="0001", cdArea="00000", lvTime="4", cdTimeFrom="2025000101")),
        ("完全失業率（％）", "0003005865",
         dict(cdTab="02", cdCat01="000", cdCat02="08", cdCat03="0", cdTimeFrom="2025000101")),
    ]
    for label, sid, cond in indicators:
        period, value, unit = latest_value(app_id, sid, **cond)
        print(f"  {label:28s}: {value}{unit}  ({period})")

    # --- lang="E" で英語のメタ情報を取得する ---
    print("\n===== 英語メタの例（lang=E） =====")
    tables = e.get_stats_list(app_id, statsCode="00200573", limit=2, lang="E")
    for t in tables:
        print(f"  [{t['@id']}] {e.text(t.get('STATISTICS_NAME'))}")


if __name__ == "__main__":
    main()
