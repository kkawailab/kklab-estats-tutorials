# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn", "jinja2", "requests", "python-multipart"]
# ///
"""FastAPI サンプル2: 統計表のメタ情報（分類の定義）を表示する Web アプリ（HTMX）。

統計表IDを入れて getMetaInfo を呼び、分類事項（CLASS_OBJ）ごとの見出しを出す。
各分類の「コード一覧」ボタンを押すと HTMX が /meta/class を呼び、その分類の
「コード↔名称↔単位」表を遅延ロードして差し込む（アプリ3の絞り込みコード調べに使う）。

実行:
    uv run scripts/fastapi_app2_metadata.py
    # 起動後ブラウザで http://127.0.0.1:8000 を開く
"""
import os

import requests
import uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from jinja2 import Template

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"
DEFAULT_APPID = os.environ.get("ESTAT_APPID", "")
MAX_CODES = 200  # 1分類あたりの表示上限（巨大分類で画面が重くならないように）

app = FastAPI(title="e-Stat メタ情報ブラウザ")


def _text(x) -> str:
    return x["$"] if isinstance(x, dict) else ("" if x is None else str(x))


def _as_list(x) -> list:
    return x if isinstance(x, list) else [x]


def get_meta_info(app_id: str, sid: str) -> tuple[str, list[dict]]:
    """getMetaInfo を呼ぶ。返り値は (表題, CLASS_OBJ のリスト)。"""
    res = requests.get(f"{BASE}/getMetaInfo",
                       params={"appId": app_id, "statsDataId": sid}, timeout=60)
    res.raise_for_status()
    body = res.json()["GET_META_INFO"]
    if body["RESULT"]["STATUS"] != 0:
        raise RuntimeError(body["RESULT"]["ERROR_MSG"])
    info = body["METADATA_INF"]
    title = _text(info["TABLE_INF"].get("TITLE"))
    return title, _as_list(info["CLASS_INF"]["CLASS_OBJ"])


PAGE = Template(
    """<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e-Stat メタ情報ブラウザ</title>
<script src="https://unpkg.com/htmx.org@2.0.4"></script>
<style>
 body{font-family:system-ui,sans-serif;max-width:860px;margin:1.5rem auto;padding:0 1rem;color:#222}
 h1{font-size:1.4rem} label{font-size:.85rem;color:#555;display:block;margin:.4rem 0 .1rem}
 input{padding:.45rem;border:1px solid #ccc;border-radius:6px;font-size:1rem}
 button{padding:.45rem .9rem;border:0;border-radius:6px;background:#005aa0;color:#fff;cursor:pointer}
 .cls{border:1px solid #e0e0e0;border-radius:8px;padding:.6rem .9rem;margin:.5rem 0}
 .cls h3{margin:.1rem 0;font-size:1rem} .cls .id{color:#5a6b7b;font-size:.8rem}
 table{border-collapse:collapse;width:100%;margin-top:.4rem;font-size:.85rem}
 th,td{border:1px solid #ddd;padding:.25rem .5rem;text-align:left}
 th{background:#f3f6f9} .err{color:#c0392b;font-weight:700}
 .htmx-indicator{display:none} .htmx-request .htmx-indicator{display:inline}
</style></head>
<body>
 <h1>e-Stat メタ情報ブラウザ</h1>
 <form hx-post="/meta" hx-target="#meta" hx-indicator="#spin">
  <label>アプリケーションID（appId）</label>
  <input type="password" name="appid" value="{{ default_appid }}" style="width:100%"
         placeholder="e-Stat で取得した API キーを貼り付け">
  <label>統計表ID（statsDataId）</label>
  <input name="sid" placeholder="例: 0003443840" style="width:100%">
  <p><button type="submit">メタ情報を取得 <span id="spin" class="htmx-indicator">…</span></button></p>
 </form>
 <div id="meta"></div>
</body></html>"""
)

CLASSES = Template(
    """<h2 style="font-size:1.1rem">{{ title or "(表題なし)" }}</h2>
{% for o in objs %}
 <div class="cls">
  <h3>{{ o.name }} <span class="id">（id={{ o.id }}, {{ o.n }}件）</span></h3>
  <button hx-get="/meta/class?appid={{ appid_q }}&sid={{ sid_q }}&id={{ o.id }}"
          hx-target="#cls-{{ o.id }}" hx-swap="innerHTML">コード一覧</button>
  <div id="cls-{{ o.id }}"></div>
 </div>
{% endfor %}"""
)

CODES = Template(
    """<table><tr><th>コード</th><th>名称</th><th>レベル</th><th>単位</th></tr>
{% for c in codes %}
 <tr><td>{{ c.code }}</td><td>{{ c.name }}</td><td>{{ c.level }}</td><td>{{ c.unit }}</td></tr>
{% endfor %}
</table>{% if capped %}<p class="id">先頭 {{ codes|length }} 件のみ表示</p>{% endif %}"""
)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return PAGE.render(default_appid=DEFAULT_APPID)


@app.post("/meta", response_class=HTMLResponse)
def meta(appid: str = Form(""), sid: str = Form("")) -> str:
    appid, sid = appid.strip(), sid.strip()
    if not appid or not sid:
        return '<p class="err">appId と統計表IDを入力してください。</p>'
    try:
        title, objs = get_meta_info(appid, sid)
    except Exception as ex:
        return f'<p class="err">エラー: {ex}</p>'
    view = [{"id": o.get("@id", ""), "name": o.get("@name", ""),
             "n": len(_as_list(o.get("CLASS", [])))} for o in objs]
    return CLASSES.render(title=title, objs=view, appid_q=appid, sid_q=sid)


@app.get("/meta/class", response_class=HTMLResponse)
def meta_class(appid: str, sid: str, id: str) -> str:
    try:
        _, objs = get_meta_info(appid, sid)
    except Exception as ex:
        return f'<p class="err">エラー: {ex}</p>'
    target = next((o for o in objs if o.get("@id") == id), None)
    if target is None:
        return '<p class="err">分類が見つかりません。</p>'
    cls = _as_list(target.get("CLASS", []))
    capped = len(cls) > MAX_CODES
    codes = [{"code": c.get("@code", ""), "name": c.get("@name", ""),
              "level": c.get("@level", "-"), "unit": c.get("@unit", "")}
             for c in cls[:MAX_CODES]]
    return CODES.render(codes=codes, capped=capped)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
