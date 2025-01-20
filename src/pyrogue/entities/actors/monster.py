"""Monster module."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Optional
import random

@dataclass
class Monster:
    """モンスターの基本クラス"""
    char: str  # 表示文字（A-Z）
    x: int
    y: int
    name: str
    level: int
    hp: int
    max_hp: int
    attack: int
    defense: int
    exp_value: int  # 倒した時の経験値
    view_range: int  # 視界範囲
    color: Tuple[int, int, int]  # 表示色
    is_hostile: bool = True  # 敵対的かどうか
    
    def move(self, dx: int, dy: int) -> None:
        """指定した方向に移動"""
        self.x += dx
        self.y += dy
    
    def take_damage(self, amount: int) -> None:
        """ダメージを受ける"""
        self.hp = max(0, self.hp - max(0, amount - self.defense))
    
    def is_dead(self) -> bool:
        """死亡しているかどうか"""
        return self.hp <= 0
    
    def heal(self, amount: int) -> None:
        """HPを回復"""
        self.hp = min(self.max_hp, self.hp + amount)
    
    def can_see_player(self, player_x: int, player_y: int, fov_map: any) -> bool:
        """プレイヤーが視界内にいるかどうか"""
        # プレイヤーまでの距離を計算
        distance = ((self.x - player_x) ** 2 + (self.y - player_y) ** 2) ** 0.5
        
        # 視界範囲内かつ、壁などで遮られていないか確認
        return (distance <= self.view_range and
                fov_map.transparent[player_y, player_x])
    
    def get_move_towards_player(self, player_x: int, player_y: int) -> Tuple[int, int]:
        """プレイヤーに向かう移動方向を取得"""
        dx = player_x - self.x
        dy = player_y - self.y
        
        # 斜め移動を含む8方向の移動を許可
        if dx != 0:
            dx = dx // abs(dx)
        if dy != 0:
            dy = dy // abs(dy)
        
        return dx, dy
    
    def get_random_move(self) -> Tuple[int, int]:
        """ランダムな移動方向を取得"""
        # 8方向のいずれかにランダムに移動
        directions = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0),           (1, 0),
            (-1, 1),  (0, 1),  (1, 1)
        ]
        return random.choice(directions) 