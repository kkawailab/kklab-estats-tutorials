# /// script
# requires-python = ">=3.11"
# dependencies = ["flet", "requests"]
# ///
"""Flet サンプル3: e-Stat の統計データを取得してランキング表示する GUI アプリ。

appID は画面上のテキスト欄に入力する。統計表ID（statsDataId）を入れて
「データ取得」を押すと getStatsData を呼び、最新の時点について値の大きい順に
並べ、横棒（バー）と表で上位を表示する。

依存ライブラリは flet と requests だけ（pandas/matplotlib は使わず、棒は
Container の幅で描く）。統計表IDはサンプル1で検索、絞り込み用のコードは
サンプル2のメタ情報ビューアで調べられる。

実行:
    uv run scripts/flet_app3_ranking.py
    flet run scripts/flet_app3_ranking.py
"""
import asyncio

import flet as ft
import requests

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"


def _as_list(x) -> list:
    return x if isinstance(x, list) else [x]


def fetch_stats_data(app_id: str, sid: str, limit: int) -> list[dict]:
    """getStatsData を呼び、コードを名称に直した tidy な行のリストを返す。

    各行は {次元名: 名称, ..., '値': float, '単位': str, '時点': str} の辞書。
    """
    params = {"appId": app_id, "statsDataId": sid, "limit": limit}
    res = requests.get(f"{BASE}/getStatsData", params=params, timeout=120)
    res.raise_for_status()
    body = res.json()["GET_STATS_DATA"]
    if body["RESULT"]["STATUS"] != 0:
        raise RuntimeError(body["RESULT"]["ERROR_MSG"])
    sdata = body["STATISTICAL_DATA"]

    # メタ（CLASS_OBJ）から「次元id → {コード: 名称}」と「次元id → 表示名」を作る
    objs = _as_list(sdata["CLASS_INF"]["CLASS_OBJ"])
    code2name = {o["@id"]: {c["@code"]: c["@name"] for c in _as_list(o["CLASS"])} for o in objs}
    id2label = {o["@id"]: o.get("@name", o["@id"]) for o in objs}

    rows = []
    for v in _as_list(sdata["DATA_INF"]["VALUE"]):
        try:
            value = float(v.get("$"))
        except (TypeError, ValueError):
            continue  # 「-」など数値化できない値は除外
        row = {"値": value, "単位": v.get("@unit", ""), "時点": ""}
        for key, code in v.items():
            if not key.startswith("@") or key == "@unit":
                continue
            dim = key[1:]                       # 例: '@cat01' → 'cat01'
            name = code2name.get(dim, {}).get(code, code)
            row[id2label.get(dim, dim)] = name
            if dim == "time":
                row["時点"] = name
        rows.append(row)
    return rows


TOP_N = 15
BAR_FULL_WIDTH = 360  # 最大値のときのバーの幅(px)


async def main(page: ft.Page) -> None:
    page.title = "e-Stat データ ランキング"
    page.window.width = 880
    page.window.height = 800
    page.scroll = ft.ScrollMode.AUTO

    app_id_field = ft.TextField(
        label="アプリケーションID（appId）",
        password=True,
        can_reveal_password=True,
    )
    sid_field = ft.TextField(label="統計表ID（statsDataId）", hint_text="例: 0003448232", expand=True)
    limit_field = ft.TextField(label="取得件数", value="500", width=110)

    status = ft.Text(color=ft.Colors.RED)
    spinner = ft.ProgressRing(visible=False, width=20, height=20)
    heading = ft.Text("", size=14, weight=ft.FontWeight.BOLD)
    bars = ft.Column(spacing=6)

    def label_for(row: dict) -> str:
        """値・単位・時点以外の次元名を連結して 1 本のバーのラベルにする。"""
        parts = [str(v) for k, v in row.items() if k not in ("値", "単位", "時点")]
        return " / ".join(parts) if parts else "(系列)"

    def render(rows: list[dict]) -> None:
        bars.controls.clear()
        if not rows:
            heading.value = "数値データが見つかりませんでした。"
            return

        # 最新の時点だけに絞る（時点コードの最大＝最も新しい）
        latest = max((r["時点"] for r in rows), default="")
        target = [r for r in rows if r["時点"] == latest] or rows
        target = sorted(target, key=lambda r: r["値"], reverse=True)[:TOP_N]

        unit = target[0]["単位"] or ""
        heading.value = f"最新時点: {latest or '不明'}    上位 {len(target)} 件（単位: {unit or '-'}）"
        vmax = max(r["値"] for r in target) or 1.0

        for r in target:
            w = max(2.0, BAR_FULL_WIDTH * r["値"] / vmax)
            bars.controls.append(
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(width=240, content=ft.Text(label_for(r), size=12, max_lines=2)),
                        ft.Container(
                            width=w, height=20, bgcolor=ft.Colors.TEAL_400, border_radius=4
                        ),
                        ft.Text(f"{r['値']:,.0f}", size=12),
                    ],
                )
            )

    async def on_fetch(e: ft.ControlEvent) -> None:
        app_id = app_id_field.value.strip()
        sid = sid_field.value.strip()
        if not app_id or not sid:
            status.value = "appId と統計表ID の両方を入力してください。"
            status.color = ft.Colors.RED
            return
        try:
            limit = max(1, min(100_000, int(limit_field.value or "500")))
        except ValueError:
            status.value = "取得件数は整数で入力してください。"
            status.color = ft.Colors.RED
            return

        status.value = ""
        heading.value = ""
        bars.controls.clear()
        spinner.visible = True
        fetch_btn.disabled = True
        page.update()

        try:
            rows = await asyncio.to_thread(fetch_stats_data, app_id, sid, limit)
        except requests.HTTPError as ex:
            status.value = f"通信エラー: {ex}"
            status.color = ft.Colors.RED
        except Exception as ex:
            status.value = f"エラー: {ex}"
            status.color = ft.Colors.RED
        else:
            status.value = f"{len(rows)} 件の数値データを取得しました。"
            status.color = ft.Colors.GREEN
            render(rows)
        finally:
            spinner.visible = False
            fetch_btn.disabled = False
            page.update()

    fetch_btn = ft.Button("データ取得", icon=ft.Icons.BAR_CHART, on_click=on_fetch)
    sid_field.on_submit = on_fetch

    page.add(
        ft.Text("e-Stat データ ランキング", size=22, weight=ft.FontWeight.BOLD),
        app_id_field,
        ft.Row([sid_field, limit_field, fetch_btn], vertical_alignment=ft.CrossAxisAlignment.END),
        ft.Row([spinner, status]),
        ft.Divider(),
        heading,
        bars,
    )


if __name__ == "__main__":
    ft.run(main)
