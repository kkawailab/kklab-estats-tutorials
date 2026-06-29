# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn", "jinja2", "requests", "python-multipart"]
# ///
"""FastAPI サンプル1: e-Stat 統計表をキーワード検索する Web アプリ（HTMX）。

appId は画面のフォーム欄に入力する（ソースに残さない）。検索すると getStatsList を
呼び、ヒットした統計表をカード一覧の HTML 断片で返し、HTMX が画面に差し込む。

実行:
    uv run scripts/fastapi_app1_search.py
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

app = FastAPI(title="e-Stat 統計表検索")


def _text(x) -> str:
    """{'@..':.., '$':'本文'} 形式のことがある値を文字列に正規化する。"""
    return x["$"] if isinstance(x, dict) else ("" if x is None else str(x))


def _as_list(x) -> list:
    """要素1件だと配列にならない API 仕様への対策。"""
    return x if isinstance(x, list) else [x]


def search_stats_list(app_id: str, word: str, limit: int) -> tuple[str, list[dict]]:
    """getStatsList を呼ぶ。返り値は (ヒット総数の文字列, 統計表のリスト)。"""
    params = {"appId": app_id, "searchWord": word, "limit": limit}
    res = requests.get(f"{BASE}/getStatsList", params=params, timeout=60)
    res.raise_for_status()
    body = res.json()["GET_STATS_LIST"]
    if body["RESULT"]["STATUS"] != 0:
        raise RuntimeError(body["RESULT"]["ERROR_MSG"])
    info = body["DATALIST_INF"]
    return str(info.get("NUMBER", "不明")), _as_list(info.get("TABLE_INF", []))


PAGE = Template(
    """<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e-Stat 統計表検索</title>
<script src="https://unpkg.com/htmx.org@2.0.4"></script>
<style>
 body{font-family:system-ui,sans-serif;max-width:820px;margin:1.5rem auto;padding:0 1rem;color:#222}
 h1{font-size:1.4rem} label{font-size:.85rem;color:#555;display:block;margin:.4rem 0 .1rem}
 input{padding:.45rem;border:1px solid #ccc;border-radius:6px;font-size:1rem}
 .row{display:flex;gap:.6rem;align-items:flex-end;flex-wrap:wrap}
 button{padding:.5rem 1rem;border:0;border-radius:6px;background:#005aa0;color:#fff;font-size:1rem;cursor:pointer}
 .card{border:1px solid #e0e0e0;border-radius:8px;padding:.7rem .9rem;margin:.5rem 0}
 .card .t{font-weight:700} .card .s{color:#5a6b7b;font-size:.85rem}
 .card .i{font-size:.8rem;color:#333;user-select:all} .err{color:#c0392b;font-weight:700}
 .htmx-indicator{display:none} .htmx-request .htmx-indicator{display:inline}
</style></head>
<body>
 <h1>e-Stat 統計表検索</h1>
 <form hx-post="/search" hx-target="#results" hx-indicator="#spin">
  <label>アプリケーションID（appId）</label>
  <input type="password" name="appid" value="{{ default_appid }}" style="width:100%"
         placeholder="e-Stat で取得した API キーを貼り付け">
  <div class="row">
   <div style="flex:1"><label>検索キーワード</label>
    <input name="word" value="人口" style="width:100%"></div>
   <div><label>件数</label><input name="limit" value="20" style="width:80px"></div>
   <button type="submit">検索 <span id="spin" class="htmx-indicator">…</span></button>
  </div>
 </form>
 <div id="results"></div>
</body></html>"""
)

RESULTS = Template(
    """<p>ヒット総数 {{ total }} 件（先頭 {{ tables|length }} 件を表示）</p>
{% for t in tables %}
 <div class="card">
  <div class="t">{{ t.title or "(表題なし)" }}</div>
  <div class="s">{{ t.stat_name }}</div>
  <div class="i">統計表ID: {{ t.id }}　調査年月: {{ t.survey or "-" }}</div>
 </div>
{% endfor %}"""
)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return PAGE.render(default_appid=DEFAULT_APPID)


@app.post("/search", response_class=HTMLResponse)
def search(appid: str = Form(""), word: str = Form(""), limit: str = Form("20")) -> str:
    appid, word = appid.strip(), word.strip()
    if not appid:
        return '<p class="err">appId を入力してください。</p>'
    if not word:
        return '<p class="err">キーワードを入力してください。</p>'
    try:
        n = max(1, min(100, int(limit or "20")))
    except ValueError:
        return '<p class="err">件数は整数で入力してください。</p>'
    try:
        total, raw = search_stats_list(appid, word, n)
    except requests.HTTPError as ex:
        return f'<p class="err">通信エラー: {ex}</p>'
    except Exception as ex:  # API エラー含む
        return f'<p class="err">エラー: {ex}</p>'
    tables = [
        {"id": t.get("@id", ""), "title": _text(t.get("TITLE")),
         "stat_name": _text(t.get("STAT_NAME")), "survey": _text(t.get("SURVEY_DATE"))}
        for t in raw
    ]
    return RESULTS.render(total=total, tables=tables)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
