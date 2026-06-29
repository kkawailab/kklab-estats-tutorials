# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pandas"]
# ///
"""例題10: 階層レベルで絞り込む（lvCat01）。

分類事項は階層構造を持つ。消費者物価指数の「品目」（cat01）は
レベル1（総合・10大費目など）→ レベル3（中分類）→ さらに細目…と深くなる。
lvCat01 を変えると、取得される品目の粒度が変わることを確かめる。

実行:
    set -a; source .env; set +a
    uv run scripts/ex10_filter_level.py
"""
import estat_api as e

SID = "0003427113"  # 消費者物価指数（2020年基準）


def main() -> None:
    app_id = e.get_app_id()

    print("lvCat01（品目の階層レベル）を変えたときに取得される品目数：\n")
    for lv in ["1", "1-2", "1-3", "1-4"]:
        sdata = e.get_stats_data(
            app_id, SID,
            cdArea="00000", cdTab="1",
            lvTime="4", cdTimeFrom="2025000101",  # 2025年以降の月次に限定して件数を抑える
            lvCat01=lv,
        )
        df = e.stats_data_to_frame(sdata)
        n_items = df["cat01_code"].nunique()
        print(f"  lvCat01={lv:4s} → 品目 {n_items:4d} 種類")

    print("\nlvCat01=1（最上位）の品目一覧の例：")
    sdata = e.get_stats_data(
        app_id, SID, cdArea="00000", cdTab="1",
        lvTime="4", cdTimeFrom="2026000101", lvCat01="1",
    )
    df = e.stats_data_to_frame(sdata)
    for name in df["cat01"].drop_duplicates().head(12):
        print(f"   ・{name}")


if __name__ == "__main__":
    main()
