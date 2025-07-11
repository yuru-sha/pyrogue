"""
設定関連のモジュール。

環境変数の読み込みと設定管理を行います。
"""

# 後方互換性のため古いCONFIGをインポート
from pyrogue.config.legacy import CONFIG

__all__ = ["CONFIG"]
