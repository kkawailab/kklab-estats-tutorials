"""matplotlib をグラフ内で日本語表示できるようにするモジュール。

import するだけで、システムにインストールされた日本語フォント
（Noto Sans CJK JP / IPAexGothic / Takao など）を自動的に選んで設定する。
外部の日本語化専用パッケージに依存すると環境差が出ることがあるため、
本書ではこの軽量モジュールを用いる。
"""
import matplotlib
from matplotlib import font_manager

# 優先的に使いたい日本語フォント（先に見つかったものを採用）
_PREFERRED = [
    "Noto Sans CJK JP", "Noto Sans JP", "IPAexGothic", "IPAPGothic",
    "TakaoPGothic", "BIZ UDPGothic", "Yu Gothic", "Hiragino Sans",
    "Meiryo", "MS Gothic", "VL PGothic",
]


def set_japanese_font() -> str | None:
    """利用可能な日本語フォントを1つ選んで matplotlib に設定する。"""
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in _PREFERRED:
        if name in available:
            matplotlib.rcParams["font.family"] = name
            matplotlib.rcParams["axes.unicode_minus"] = False  # 軸のマイナス記号化け対策
            return name
    return None


# import された時点で自動設定する
set_japanese_font()
