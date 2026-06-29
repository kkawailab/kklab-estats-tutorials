# /// script
# requires-python = ">=3.11"
# dependencies = ["flet", "requests"]
# ///
"""Flet サンプル2: e-Stat API で統計表のメタ情報を表示する GUI アプリ。

appID は画面上のテキスト欄に入力する。統計表ID（statsDataId）を入れて
「メタ情報取得」を押すと getMetaInfo を呼び、分類事項（CLASS_OBJ）ごとに
折りたたみパネルを作り、その中に「コード ↔ 名称」の表を表示する。

getStatsData を絞り込むときに使う cdTab / cdCat01 / cdArea などのコードを
調べるのに便利。統計表IDはサンプル1（flet_app1_search.py）で探せる。

実行:
    uv run scripts/flet_app2_metadata.py
    flet run scripts/flet_app2_metadata.py
"""
import asyncio

import flet as ft
import requests

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"


def _as_list(x) -> list:
    return x if isinstance(x, list) else [x]


def get_meta_info(app_id: str, sid: str) -> tuple[str, list[dict]]:
    """getMetaInfo を同期的に呼び (統計表タイトル, CLASS_OBJ のリスト) を返す。"""
    params = {"appId": app_id, "statsDataId": sid}
    res = requests.get(f"{BASE}/getMetaInfo", params=params, timeout=60)
    res.raise_for_status()
    body = res.json()["GET_META_INFO"]
    if body["RESULT"]["STATUS"] != 0:
        raise RuntimeError(body["RESULT"]["ERROR_MSG"])
    meta = body["METADATA_INF"]
    title = meta["TABLE_INF"]["TITLE"]
    title = title["$"] if isinstance(title, dict) else str(title)
    objs = _as_list(meta["CLASS_INF"]["CLASS_OBJ"])
    return title, objs


# 1分類あたり表に出すコード数の上限（大きい分類で画面が重くなるのを防ぐ）
MAX_ROWS = 50


async def main(page: ft.Page) -> None:
    page.title = "e-Stat メタ情報ビューア"
    page.window.width = 820
    page.window.height = 760
    page.scroll = ft.ScrollMode.AUTO

    app_id_field = ft.TextField(
        label="アプリケーションID（appId）",
        password=True,
        can_reveal_password=True,
    )
    sid_field = ft.TextField(
        label="統計表ID（statsDataId）",
        hint_text="例: 0003448232",
        expand=True,
    )

    status = ft.Text(color=ft.Colors.RED)
    spinner = ft.ProgressRing(visible=False, width=20, height=20)
    title_text = ft.Text("", size=15, weight=ft.FontWeight.BOLD, selectable=True)
    panels = ft.Column(spacing=4)

    def build_panel(obj: dict) -> ft.ExpansionTile:
        """1つの分類事項（CLASS_OBJ）を折りたたみパネルにする。"""
        classes = _as_list(obj["CLASS"])
        rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(c.get("@code", ""), selectable=True)),
                    ft.DataCell(ft.Text(c.get("@name", ""), selectable=True)),
                    ft.DataCell(ft.Text(c.get("@unit", "") or "-")),
                ]
            )
            for c in classes[:MAX_ROWS]
        ]
        table = ft.DataTable(
            columns=[
                ft.DataColumn(label=ft.Text("コード")),
                ft.DataColumn(label=ft.Text("名称")),
                ft.DataColumn(label=ft.Text("単位")),
            ],
            rows=rows,
            column_spacing=24,
        )
        note = ""
        if len(classes) > MAX_ROWS:
            note = f"（全 {len(classes)} 件中、先頭 {MAX_ROWS} 件を表示）"
        return ft.ExpansionTile(
            title=ft.Text(f"@{obj.get('@id', '')} : {obj.get('@name', '')}  〔{len(classes)}件〕"),
            subtitle=ft.Text(note) if note else None,
            controls=[ft.Container(content=table, padding=ft.Padding.only(left=12, bottom=8))],
        )

    async def on_fetch(e: ft.ControlEvent) -> None:
        app_id = app_id_field.value.strip()
        sid = sid_field.value.strip()
        if not app_id:
            status.value = "appId を入力してください。"
            status.color = ft.Colors.RED
            return
        if not sid:
            status.value = "統計表ID（statsDataId）を入力してください。"
            status.color = ft.Colors.RED
            return

        status.value = ""
        title_text.value = ""
        panels.controls.clear()
        spinner.visible = True
        fetch_btn.disabled = True
        page.update()

        try:
            title, objs = await asyncio.to_thread(get_meta_info, app_id, sid)
        except requests.HTTPError as ex:
            status.value = f"通信エラー: {ex}"
            status.color = ft.Colors.RED
        except Exception as ex:
            status.value = f"エラー: {ex}"
            status.color = ft.Colors.RED
        else:
            title_text.value = title
            status.value = f"分類事項 {len(objs)} 種類を取得しました。"
            status.color = ft.Colors.GREEN
            for obj in objs:
                panels.controls.append(build_panel(obj))
        finally:
            spinner.visible = False
            fetch_btn.disabled = False
            page.update()

    fetch_btn = ft.Button("メタ情報取得", icon=ft.Icons.INFO_OUTLINE, on_click=on_fetch)
    sid_field.on_submit = on_fetch

    page.add(
        ft.Text("e-Stat メタ情報ビューア", size=22, weight=ft.FontWeight.BOLD),
        app_id_field,
        ft.Row([sid_field, fetch_btn], vertical_alignment=ft.CrossAxisAlignment.END),
        ft.Row([spinner, status]),
        ft.Divider(),
        title_text,
        panels,
    )


if __name__ == "__main__":
    ft.run(main)
