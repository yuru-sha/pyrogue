"""
スコアランキング管理モジュール。

オリジナルRogue風のスコアランキングシステムを提供します。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogue.entities.actors.player import Player


class ScoreEntry:
    """スコアエントリー"""

    def __init__(
        self,
        player_name: str,
        score: int,
        level: int,
        deepest_floor: int,
        gold: int,
        monsters_killed: int,
        turns_played: int,
        death_cause: str,
        game_result: str,  # "victory" or "death"
        timestamp: str,
    ) -> None:
        self.player_name = player_name
        self.score = score
        self.level = level
        self.deepest_floor = deepest_floor
        self.gold = gold
        self.monsters_killed = monsters_killed
        self.turns_played = turns_played
        self.death_cause = death_cause
        self.game_result = game_result
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        """辞書形式で返す"""
        return {
            "player_name": self.player_name,
            "score": self.score,
            "level": self.level,
            "deepest_floor": self.deepest_floor,
            "gold": self.gold,
            "monsters_killed": self.monsters_killed,
            "turns_played": self.turns_played,
            "death_cause": self.death_cause,
            "game_result": self.game_result,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ScoreEntry:
        """辞書から作成"""
        try:
            return cls(
                player_name=data.get("player_name", "Unknown"),
                score=data.get("score", 0),
                level=data.get("level", 1),
                deepest_floor=data.get("deepest_floor", 1),
                gold=data.get("gold", 0),
                monsters_killed=data.get("monsters_killed", 0),
                turns_played=data.get("turns_played", 0),
                death_cause=data.get("death_cause", "Unknown"),
                game_result=data.get("game_result", "Unknown"),
                timestamp=data.get("timestamp", "Unknown"),
            )
        except Exception as e:
            # デフォルト値でフォールバック
            return cls(
                player_name="Corrupted Entry",
                score=0,
                level=1,
                deepest_floor=1,
                gold=0,
                monsters_killed=0,
                turns_played=0,
                death_cause=f"Data corruption: {e}",
                game_result="Error",
                timestamp="Unknown",
            )


class ScoreManager:
    """スコアランキング管理クラス"""

    def __init__(self, score_file: str = "scores.json") -> None:
        self.score_file = score_file
        self.scores: list[ScoreEntry] = []
        self.load_scores()

    def load_scores(self) -> None:
        """スコアファイルから読み込み"""
        if not os.path.exists(self.score_file):
            return

        try:
            with open(self.score_file, encoding="utf-8") as f:
                data = json.load(f)
                self.scores = [ScoreEntry.from_dict(entry) for entry in data]
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            self.scores = []

    def save_scores(self) -> None:
        """スコアファイルに保存"""
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(self.score_file), exist_ok=True)

            with open(self.score_file, "w", encoding="utf-8") as f:
                json.dump(
                    [entry.to_dict() for entry in self.scores],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except OSError:
            pass  # ファイル保存に失敗してもゲームは続行

    def add_score(
        self,
        player: Player,
        death_cause: str = "Unknown",
        game_result: str = "death",
        player_name: str = "Player",
    ) -> None:
        """スコアを追加"""
        entry = ScoreEntry(
            player_name=player_name,
            score=player.calculate_score(),
            level=player.level,
            deepest_floor=player.deepest_floor,
            gold=player.gold,
            monsters_killed=player.monsters_killed,
            turns_played=player.turns_played,
            death_cause=death_cause,
            game_result=game_result,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        self.scores.append(entry)
        # スコア順にソート（降順）
        self.scores.sort(key=lambda x: x.score, reverse=True)
        # 上位100件のみ保持
        self.scores = self.scores[:100]
        self.save_scores()

    def get_top_scores(self, limit: int = 10) -> list[ScoreEntry]:
        """上位スコアを取得"""
        return self.scores[:limit]

    def get_rank(self, score: int) -> int:
        """指定スコアの順位を取得"""
        rank = 1
        for entry in self.scores:
            if score >= entry.score:
                return rank
            rank += 1
        return rank

    def get_high_score(self) -> int:
        """最高スコアを取得"""
        if not self.scores:
            return 0
        return self.scores[0].score

    def format_score_table(self, limit: int = 10) -> str:
        """スコアテーブルを文字列形式で返す"""
        if not self.scores:
            return "No scores recorded yet."

        lines = ["Top Scores:"]
        lines.append("-" * 80)
        lines.append(
            f"{'Rank':<4} {'Name':<12} {'Score':<8} {'Lv':<3} {'Floor':<5} {'Gold':<6} {'Kills':<5} {'Result':<8} {'Date':<16}"
        )
        lines.append("-" * 80)

        for i, entry in enumerate(self.get_top_scores(limit)):
            rank = i + 1
            result = "Victory" if entry.game_result == "victory" else "Death"
            lines.append(
                f"{rank:<4} {entry.player_name:<12} {entry.score:<8} {entry.level:<3} {entry.deepest_floor:<5} "
                f"{entry.gold:<6} {entry.monsters_killed:<5} {result:<8} {entry.timestamp[:16]}"
            )

        return "\n".join(lines)
