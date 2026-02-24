"""
规则配置模块
"""

from enum import Enum


class RuleSet(Enum):
    """规则集"""

    JAPANESE = "japanese"  # 日本麻将标准规则
    TENHOU = "tenhou"  # 天凤规则
    MAHJONG_SOUL = "mahjong_soul"  # 雀魂规则


class GameRules:
    """
    游戏规则配置

    可配置不同平台的规则差异
    """

    def __init__(self, rule_set: RuleSet = RuleSet.JAPANESE):
        """
        初始化规则配置

        Args:
            rule_set: 规则集
        """
        self.rule_set = rule_set

        # 基本规则
        self.allow_aka_dora = True  # 是否允许赤宝牌
        self.starting_points = 25000  # 起始点数

        # 役种规则
        self.allow_open_tanyao = True  # 是否允许副露断幺九
        self.allow_kuitan = True  # 喰い断（副露断幺九）

        # 立直规则
        self.riichi_cost = 1000  # 立直棒

        # 本场规则
        self.honba_tsumo_bonus = 300  # 本场自摸额外点数
        self.honba_ron_bonus = 300  # 本场荣和额外点数

        # 流局规则
        self.nagashi_mangan = True  # 是否有流局满贯

        # 根据不同规则集调整
        self._apply_rule_set()

    def _apply_rule_set(self):
        """应用特定规则集的配置"""
        if self.rule_set == RuleSet.TENHOU:
            # 天凤规则
            self.allow_aka_dora = True
            self.allow_open_tanyao = True

        elif self.rule_set == RuleSet.MAHJONG_SOUL:
            # 雀魂规则
            self.allow_aka_dora = True
            self.allow_open_tanyao = True
            self.starting_points = 25000


# 默认规则
DEFAULT_RULES = GameRules(RuleSet.JAPANESE)
