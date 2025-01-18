"""Player module."""
from dataclasses import dataclass

@dataclass
class Player:
    """プレイヤーを表すクラス"""
    x: int = 0
    y: int = 0
    hp: int = 20
    max_hp: int = 20
    attack: int = 5
    defense: int = 3
    level: int = 1
    exp: int = 0
    hunger: int = 100  # 満腹度（100が最大）
    gold: int = 0

    def move(self, dx: int, dy: int) -> None:
        """指定した方向に移動"""
        self.x += dx
        self.y += dy

    def take_damage(self, amount: int) -> None:
        """ダメージを受ける"""
        self.hp = max(0, self.hp - max(0, amount - self.defense))

    def heal(self, amount: int) -> None:
        """HPを回復"""
        self.hp = min(self.max_hp, self.hp + amount)

    def gain_exp(self, amount: int) -> bool:
        """経験値を獲得
        
        Returns:
            bool: レベルアップした場合はTrue
        """
        self.exp += amount
        if self.exp >= self.level * 100:  # 簡単な経験値テーブル
            self.level_up()
            return True
        return False

    def level_up(self) -> None:
        """レベルアップ時の処理"""
        self.level += 1
        self.max_hp += 5
        self.hp = self.max_hp
        self.attack += 2
        self.defense += 1
        self.exp = 0  # 経験値リセット

    def consume_food(self, amount: int = 1) -> None:
        """食料を消費（満腹度が減少）"""
        self.hunger = max(0, self.hunger - amount)

    def eat_food(self, amount: int = 25) -> None:
        """食料を食べる（満腹度が回復）"""
        self.hunger = min(100, self.hunger + amount) 