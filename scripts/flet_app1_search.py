# /// script
# requires-python = ">=3.11"
# dependencies = ["flet", "requests"]
# ///
"""Flet サンプル1: e-Stat API で統計表をキーワード検索する GUI アプリ。

appID（アプリケーションID）はアプリ起動後に画面上のテキスト欄へ入力する。
キーワードを入れて「検索」を押すと getStatsList を呼び、ヒットした統計表を
一覧（スクロール可能なリスト）に表示する。

実行:
    uv run scripts/flet_app1_search.py            # デスクトップウィンドウで起動
    # もしくは
    flet run scripts/flet_app1_search.py          # 同上
    flet run --web scripts/flet_app1_search.py    # ブラウザで起動

appID は https://www.e-stat.go.jp/api/ で取得（無料登録）。
"""
import asyncio

import flet as ft
import requests

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"


def _text(x) -> str:
    """{'@...':.., '$':'本文'} 形式のことがある値を文字列に正規化する。"""
    return x["$"] if isinstance(x, dict) else ("" if x is None else str(x))


def _as_list(x) -> list:
    """要素1件だと配列にならない API 仕様への対策。"""
    return x if isinstance(x, list) else [x]


def search_stats_list(app_id: str, word: str, limit: int) -> tuple[str, list[dict]]:
    """getStatsList を同期的に呼ぶ（呼び出し側で別スレッド実行する）。

    返り値は (ヒット総数の文字列, 統計表のリスト)。エラーは例外で送出する。
    """
    params = {"appId": app_id, "searchWord": word, "limit": limit}
    res = requests.get(f"{BASE}/getStatsList", params=params, timeout=60)
    res.raise_for_status()
    body = res.json()["GET_STATS_LIST"]
    if body["RESULT"]["STATUS"] != 0:
        raise RuntimeError(body["RESULT"]["ERROR_MSG"])
    info = body["DATALIST_INF"]
    total = str(info.get("NUMBER", "不明"))
    return total, _as_list(info.get("TABLE_INF", []))


async def main(page: ft.Page) -> None:
    page.title = "e-Stat 統計表検索"
    page.window.width = 760
    page.window.height = 720
    page.scroll = ft.ScrollMode.AUTO

    # --- 入力欄 ---
    app_id_field = ft.TextField(
        label="アプリケーションID（appId）",
        hint_text="e-Stat で取得した API キーを貼り付け",
        password=True,
        can_reveal_password=True,
    )
    word_field = ft.TextField(label="検索キーワード", value="人口", expand=True)
    limit_field = ft.TextField(label="件数", value="20", width=90)

    status = ft.Text(color=ft.Colors.RED)
    spinner = ft.ProgressRing(visible=False, width=20, height=20)
    results = ft.ListView(expand=True, spacing=6, padding=4)

    async def on_search(e: ft.ControlEvent) -> None:
        app_id = app_id_field.value.strip()
        word = word_field.value.strip()
        if not app_id:
            status.value = "appId を入力してください。"
            return
        if not word:
            status.value = "キーワードを入力してください。"
            return
        try:
            limit = max(1, min(100, int(limit_field.value or "20")))
        except ValueError:
            status.value = "件数は整数で入力してください。"
            return

        # 検索中の表示にする
        status.value = ""
        results.controls.clear()
        spinner.visible = True
        search_btn.disabled = True
        page.update()

        try:
            # requests はブロッキングなので別スレッドで実行し UI を固めない
            total, tables = await asyncio.to_thread(search_stats_list, app_id, word, limit)
        except requests.HTTPError as ex:
            status.value = f"通信エラー: {ex}"
        except Exception as ex:  # API エラー含む
            status.value = f"エラー: {ex}"
        else:
            status.value = f"ヒット総数 {total} 件（先頭 {len(tables)} 件を表示）"
            status.color = ft.Colors.GREEN
            for t in tables:
                stat_name = _text(t.get("STAT_NAME"))
                title = _text(t.get("TITLE"))
                survey = _text(t.get("SURVEY_DATE"))
                results.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=10,
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(title or "(表題なし)", weight=ft.FontWeight.BOLD),
                                    ft.Text(stat_name, size=12, color=ft.Colors.BLUE_GREY),
                                    ft.Text(
                                        f"統計表ID: {t.get('@id', '')}    調査年月: {survey or '-'}",
                                        size=11,
                                        selectable=True,
                                    ),
                                ],
                            ),
                        )
                    )
                )
        finally:
            spinner.visible = False
            search_btn.disabled = False
            page.update()

    search_btn = ft.Button("検索", icon=ft.Icons.SEARCH, on_click=on_search)
    word_field.on_submit = on_search

    page.add(
        ft.Text("e-Stat 統計表検索", size=22, weight=ft.FontWeight.BOLD),
        app_id_field,
        ft.Row([word_field, limit_field, search_btn], vertical_alignment=ft.CrossAxisAlignment.END),
        ft.Row([spinner, status]),
        ft.Divider(),
        ft.Container(content=results, expand=True, height=420),
    )


if __name__ == "__main__":
    ft.run(main)
