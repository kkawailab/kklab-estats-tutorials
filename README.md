# e-Stat API チュートリアル

政府統計の総合窓口 **e-Stat** が提供する **API 機能（バージョン 3.0）** を使い、
Python から公的統計データを検索・取得・整形・可視化する手順を学ぶ入門チュートリアルです。
本文 PDF と同じコードを `scripts/` に置いているため、解説を読みながら実際の API 呼び出しを再現できます。

- API の仕組み、利用登録、リクエスト、レスポンス構造、ページング、エラー処理を順に解説
- 各種データを入手する **30 個の実践例題**（人口・労働・物価・家計・GDP・産業・企業・教育など）
- 付録として、コーディングエージェント用プロンプト集、Flet GUI アプリ、FastAPI + HTMX Web アプリを収録
- Python の実行は **uv** ＋ **PEP 723**（インラインスクリプトメタデータ）形式で、依存関係を手動管理せずに実行可能
- 完成版チュートリアルを **PDF**（`estats-tutorial.pdf`）として同梱（日本語 LuaLaTeX で組版）

**著者:** 河合勝彦（名古屋市立大学大学院経済学研究科, kkawai@econ.nagoya-cu.ac.jp）

> 本リポジトリは、**完成版 PDF と実行可能なサンプルスクリプト**の配布版です。
> 解説の本文は同梱の `estats-tutorial.pdf` をご覧ください。

---

## 1. 必要な環境

| ツール | 用途 | 確認コマンド |
|--------|------|--------------|
| [uv](https://docs.astral.sh/uv/) | Python スクリプトの実行・依存管理 | `uv --version` |
| e-Stat **appId** | API 認証（無料・要登録） | — |

> スクリプトが依存する Python パッケージ（`requests`, `pandas`, `matplotlib` など）は
> 各スクリプトの PEP 723 メタデータに記述されており、`uv run` 実行時に自動でインストールされます。
> 手動の `pip install` は不要です。

---

## 2. e-Stat appId の取得

1. <https://www.e-stat.go.jp/api/> にアクセスし、利用登録（メールアドレス登録）を行う
2. ログイン後、マイページの「**API機能（アプリケーションIDの取得）**」を開く
3. アプリケーション名・URL・概要を入力して登録すると **appId** が発行される
   （公開予定のないアプリでも `http://test.localhost/` などのURLで登録可）

詳しい手順は同梱 PDF の本文（第1部 第2節）で解説しています。

---

## 3. セットアップ

```bash
# リポジトリのルートで
cp .env.example .env
# .env を編集して ESTAT_APPID に発行された appId を設定する
```

---

## 4. スクリプトの実行

各スクリプトは単体で実行できます。実行前に appId を環境変数として読み込みます。

```bash
set -a; source .env; set +a          # ESTAT_APPID を環境変数に展開
uv run scripts/ex01_search_statslist.py
```

例題（`ex01`〜`ex30`）をまとめて実行する場合:

```bash
set -a; source .env; set +a
for f in scripts/ex*.py; do echo "===== $f ====="; uv run "$f" || break; done
```

グラフを生成する例題は `figures/` に画像を、CSV 等を書き出す例題は `output/`（自動生成）に
ファイルを保存します。

付録のサンプルアプリは個別に起動します（長時間稼働する GUI / Web サーバ）。

```bash
uv run scripts/flet_app1_search.py        # Flet GUI アプリ
uv run scripts/fastapi_app1_search.py     # FastAPI + HTMX Web アプリ（127.0.0.1:8000）
```

---

## 5. ディレクトリ構成

```
kklab-estats-tutorials/
├── README.md              # このファイル
├── estats-tutorial.pdf    # 完成版チュートリアル（PDF・本文）
├── .env.example           # appId 設定のひな形（.env にコピーして使う）
├── .gitignore
├── scripts/               # PEP 723 スクリプト（文書掲載元＝実行元）
│   ├── ex01_*.py ... ex30_*.py   # 30 個の実践例題
│   ├── estat_api.py / jpfont.py  # 共通ヘルパ
│   ├── flet_app*.py              # 付録: Flet GUI アプリ
│   └── fastapi_app*.py           # 付録: FastAPI + HTMX Web アプリ
└── figures/               # 例題が生成した図（サンプル）
```

---

## 6. 出典・ライセンス

- 本チュートリアルで取得・表示する統計データの出典は **「政府統計の総合窓口(e-Stat)」**
  （<https://www.e-stat.go.jp/>）です。API の利用にあたっては
  [e-Stat API 機能の利用規約](https://www.e-stat.go.jp/api/terms-of-use) に従ってください。
- e-Stat API を用いたアプリケーション・成果物には、上記の出典表示（クレジット）が求められます。
