# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn", "jinja2", "requests", "python-multipart", "pandas"]
# ///
"""FastAPI サンプル3: e-Stat 統計データのダッシュボード（HTMX + Chart.js + CSV）。

統計表IDと絞り込みコード（cdTab など）を入れて getStatsData を呼び、コードを名称に
変換して pandas で整形。最新時点の上位を「表」と「棒グラフ（Chart.js）」で表示し、
整形済みデータを CSV でダウンロードできる。getStatsList→getMetaInfo→getStatsData の
締めくくりとなる“本格アプリ”。アプリ1で見つけた統計表ID、アプリ2で調べたコードを使う。

実行:
    uv run scripts/fastapi_app3_dashboard.py
    # 起動後ブラウザで http://127.0.0.1:8000 を開く
"""
import io
import json
import os
from urllib.parse import urlencode

import pandas as pd
import requests
import uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, Response
from jinja2 import Template

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"
DEFAULT_APPID = os.environ.get("ESTAT_APPID", "")
MAX_PAGES = 10   # NEXT_KEY を辿る最大ページ数（暴走防止）
TOP_N = 20       # グラフ・表に出す上位件数

app = FastAPI(title="e-Stat データ・ダッシュボード")


def _text(x) -> str:
    return x["$"] if isinstance(x, dict) else ("" if x is None else str(x))


def _as_list(x) -> list:
    return x if isinstance(x, list) else [x]


def get_stats_data(app_id: str, sid: str, **filters) -> dict:
    """getStatsData を呼び、NEXT_KEY を辿って（最大 MAX_PAGES）全件結合する。"""
    base = {"appId": app_id, "statsDataId": sid,
            **{k: v for k, v in filters.items() if v}}

    def fetch(params: dict) -> dict:
        res = requests.get(f"{BASE}/getStatsData", params=params, timeout=120)
        res.raise_for_status()
        body = res.json()["GET_STATS_DATA"]
        if body["RESULT"]["STATUS"] != 0:
            raise RuntimeError(body["RESULT"]["ERROR_MSG"])
        return body["STATISTICAL_DATA"]

    sdata = fetch(base)
    values = _as_list(sdata["DATA_INF"]["VALUE"])
    next_key = sdata["RESULT_INF"].get("NEXT_KEY")
    pages = 1
    while next_key and pages < MAX_PAGES:
        sd2 = fetch({**base, "startPosition": next_key})
        values += _as_list(sd2["DATA_INF"]["VALUE"])
        next_key = sd2["RESULT_INF"].get("NEXT_KEY")
        pages += 1
    sdata["DATA_INF"]["VALUE"] = values
    return sdata


def to_table(sdata: dict) -> pd.DataFrame:
    """STATISTICAL_DATA を tidy な DataFrame に。各次元名・<id>_code・値・単位。"""
    objs = _as_list(sdata["CLASS_INF"]["CLASS_OBJ"])
    code2name = {o["@id"]: {c["@code"]: c["@name"] for c in _as_list(o["CLASS"])}
                 for o in objs}
    raw = pd.DataFrame(_as_list(sdata["DATA_INF"]["VALUE"]))
    out: dict[str, object] = {}
    for col in raw.columns:
        if col == "$":
            out["値"] = pd.to_numeric(raw[col], errors="coerce")
        elif col == "@unit":
            out["単位"] = raw[col]
        elif col.startswith("@"):
            key = col[1:]
            out[f"{key}_code"] = raw[col]
            if key in code2name:
                out[key] = raw[col].map(code2name[key])
    return pd.DataFrame(out)


def build_series(df: pd.DataFrame) -> dict:
    """最新時点の上位 TOP_N をグラフ用 {labels, values, unit, period} にする。"""
    df = df.dropna(subset=["値"]).copy()
    period = ""
    if "time_code" in df.columns:
        latest = df["time_code"].max()
        df = df[df["time_code"] == latest]
        period = str(df["time"].iloc[0]) if "time" in df.columns and len(df) else str(latest)
    name_cols = [c for c in df.columns
                 if c not in ("値", "単位", "time") and not c.endswith("_code")]
    if name_cols:
        labels = df[name_cols].astype(str).agg(" / ".join, axis=1)
    else:
        labels = df.index.astype(str)
    df = df.assign(__label=labels).sort_values("値", ascending=False).head(TOP_N)
    unit = str(df["単位"].iloc[0]) if "単位" in df.columns and len(df) else ""
    return {"labels": df["__label"].tolist(),
            "values": [float(v) for v in df["値"].tolist()],
            "unit": unit, "period": period}


PAGE = Template(
    """<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e-Stat データ・ダッシュボード</title>
<script src="https://unpkg.com/htmx.org@2.0.4"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
 body{font-family:system-ui,sans-serif;max-width:920px;margin:1.5rem auto;padding:0 1rem;color:#222}
 h1{font-size:1.4rem} label{font-size:.85rem;color:#555;display:block;margin:.4rem 0 .1rem}
 input{padding:.45rem;border:1px solid #ccc;border-radius:6px;font-size:1rem}
 .row{display:flex;gap:.6rem;flex-wrap:wrap} .row>div{flex:1;min-width:120px}
 button{padding:.5rem 1rem;border:0;border-radius:6px;background:#005aa0;color:#fff;cursor:pointer}
 table{border-collapse:collapse;width:100%;margin-top:.6rem;font-size:.85rem}
 th,td{border:1px solid #ddd;padding:.25rem .5rem} th{background:#f3f6f9}
 td.num{text-align:right;font-variant-numeric:tabular-nums} .err{color:#c0392b;font-weight:700}
 .htmx-indicator{display:none} .htmx-request .htmx-indicator{display:inline}
 a.csv{display:inline-block;margin:.5rem 0;color:#005aa0}
</style></head>
<body>
 <h1>e-Stat データ・ダッシュボード</h1>
 <form hx-post="/dashboard" hx-target="#panel" hx-indicator="#spin">
  <label>アプリケーションID（appId）</label>
  <input type="password" name="appid" value="{{ default_appid }}" style="width:100%"
         placeholder="e-Stat で取得した API キーを貼り付け">
  <label>統計表ID（statsDataId）</label>
  <input name="sid" placeholder="例: 0003443840" style="width:100%">
  <div class="row">
   <div><label>cdTab</label><input name="cdTab" placeholder="表章(任意)"></div>
   <div><label>cdCat01</label><input name="cdCat01" placeholder="分類1(任意)"></div>
   <div><label>cdArea</label><input name="cdArea" placeholder="地域(任意)"></div>
   <div><label>cdTime</label><input name="cdTime" placeholder="時間(任意)"></div>
  </div>
  <p><button type="submit">表示 <span id="spin" class="htmx-indicator">…</span></button></p>
 </form>
 <canvas id="chart" height="120"></canvas>
 <div id="panel"></div>
 <script>
  let _chart = null;
  function renderChart(){
    const el = document.getElementById("chart-data");
    if(!el) return;
    const d = JSON.parse(el.textContent);
    const ctx = document.getElementById("chart");
    if(_chart) _chart.destroy();
    _chart = new Chart(ctx, {
      type: "bar",
      data: { labels: d.labels,
              datasets: [{ label: (d.unit || "値") + " (" + d.period + ")",
                           data: d.values, backgroundColor: "#4C72B0" }] },
      options: { indexAxis: "y", responsive: true,
                 plugins: { legend: { display: true } } }
    });
  }
  document.body.addEventListener("htmx:afterSwap", function(e){
    if(e.detail.target.id === "panel") renderChart();
  });
 </script>
</body></html>"""
)

PANEL = Template(
    """<p>{{ title }} ― {{ period }} 時点の上位 {{ rows|length }} 件</p>
<a class="csv" href="{{ csv_url }}">CSV ダウンロード</a>
<table><tr><th>項目</th><th>値</th><th>単位</th></tr>
{% for r in rows %}
 <tr><td>{{ r.label }}</td><td class="num">{{ "{:,.0f}".format(r.value) }}</td><td>{{ unit }}</td></tr>
{% endfor %}
</table>
<script type="application/json" id="chart-data">{{ chart_json }}</script>"""
)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return PAGE.render(default_appid=DEFAULT_APPID)


@app.post("/dashboard", response_class=HTMLResponse)
def dashboard(appid: str = Form(""), sid: str = Form(""),
              cdTab: str = Form(""), cdCat01: str = Form(""),
              cdArea: str = Form(""), cdTime: str = Form("")) -> str:
    appid, sid = appid.strip(), sid.strip()
    if not appid or not sid:
        return '<p class="err">appId と統計表IDを入力してください。</p>'
    filters = {"cdTab": cdTab, "cdCat01": cdCat01, "cdArea": cdArea, "cdTime": cdTime}
    try:
        sdata = get_stats_data(appid, sid, **filters)
        df = to_table(sdata)
        series = build_series(df)
    except Exception as ex:
        return f'<p class="err">エラー: {ex}</p>'
    title = _text(sdata.get("TABLE_INF", {}).get("TITLE")) or sid
    rows = [{"label": l, "value": v} for l, v in zip(series["labels"], series["values"])]
    csv_url = "/download.csv?" + urlencode({"appid": appid, "sid": sid, **filters})
    return PANEL.render(title=title, period=series["period"], unit=series["unit"],
                        rows=rows, chart_json=json.dumps(series, ensure_ascii=False),
                        csv_url=csv_url)


@app.get("/download.csv")
def download_csv(appid: str, sid: str, cdTab: str = "", cdCat01: str = "",
                 cdArea: str = "", cdTime: str = "") -> Response:
    filters = {"cdTab": cdTab, "cdCat01": cdCat01, "cdArea": cdArea, "cdTime": cdTime}
    try:
        sdata = get_stats_data(appid, sid, **filters)
        df = to_table(sdata)
    except Exception as ex:
        return Response(f"error,{ex}\n", media_type="text/csv", status_code=502)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return Response(
        buf.getvalue().encode("utf-8-sig"),  # Excel 文字化け対策で BOM 付き
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{sid}.csv"'},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
