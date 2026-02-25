"""
符数计算模块
"""

from typing import List
from .tiles import Tile, Meld, MeldType
from .parser import MentsuPattern


class FuCalculator:
    """
    符数计算器

    符数计算规则：
    - 基础符：20符
    - 门清荣和：10符
    - 自摸：2符
    - 雀头：
      - 役牌雀头：2符
      - 连风雀头：4符
    - 面子符：
      - 明刻（中张）：2符
      - 明刻（幺九）：4符
      - 暗刻（中张）：4符
      - 暗刻（幺九）：8符
      - 明杠（中张）：8符
      - 明杠（幺九）：16符
      - 暗杠（中张）：16符
      - 暗杠（幺九）：32符
    - 听牌形式：
      - 边张、坎张、单骑：2符
    - 平和自摸：固定20符
    - 七对子：固定25符
    """

    def calculate(
        self,
        pattern: MentsuPattern,
        win_tile: Tile,
        is_tsumo: bool,
        is_menzen: bool,
        is_pinfu: bool,
        is_chiitoitsu: bool,
        seat_wind: str = "E",
        prevalent_wind: str = "E",
        melds: List[Meld] = None,
    ) -> int:
        """
        计算符数

        Args:
            pattern: 面子组合模式
            win_tile: 和牌
            is_tsumo: 是否自摸
            is_menzen: 是否门前清
            is_pinfu: 是否平和
            is_chiitoitsu: 是否七对子
            seat_wind: 自风
            prevalent_wind: 场风
            melds: 副露列表

        Returns:
            符数（向上取整到10）
        """
        # 七对子固定25符
        if is_chiitoitsu:
            return 25

        # 平和自摸固定20符
        if is_pinfu and is_tsumo:
            return 20

        fu = 0

        # 基础符
        fu += 20

        # 门清荣和加10符
        if is_menzen and not is_tsumo:
            fu += 10

        # 自摸加2符（平和自摸除外，已经在上面处理）
        if is_tsumo and not is_pinfu:
            fu += 2

        # 雀头符
        if pattern.jantou:
            jantou_tile = pattern.jantou[0]
            fu += self._calculate_jantou_fu(jantou_tile, seat_wind, prevalent_wind)

        # ---- 暗刻符 ----
        for koutsu in pattern.koutsu:
            tile = koutsu[0]
            # 荣和时，如果和牌刚好组成这个刻子，则视为明刻
            if not is_tsumo and win_tile == tile:
                fu += self._calculate_koutsu_fu(
                    tile, is_anko=False, is_terminal=tile.is_terminal()
                )
            else:
                fu += self._calculate_koutsu_fu(
                    tile, is_anko=True, is_terminal=tile.is_terminal()
                )

        # ---- 明刻符（碰） ----
        for koutsu in pattern.open_koutsu:
            tile = koutsu[0]
            fu += self._calculate_koutsu_fu(
                tile, is_anko=False, is_terminal=tile.is_terminal()
            )

        # ---- 明杠符 ----
        for kantsu in pattern.min_kantsu:
            tile = kantsu[0]
            if tile.is_terminal():
                fu += 16  # 幺九明杠
            else:
                fu += 8  # 中张明杠

        # ---- 暗杠符 ----
        for kantsu in pattern.ankan:
            tile = kantsu[0]
            if tile.is_terminal():
                fu += 32  # 幺九暗杠
            else:
                fu += 16  # 中张暗杠

        # 听牌形式符（边张、坎张、单骑）
        fu += self._calculate_wait_fu(pattern, win_tile)

        # 向上取整到10
        if fu > 20:
            fu = ((fu + 9) // 10) * 10

        return fu

    def _calculate_jantou_fu(
        self, jantou_tile: Tile, seat_wind: str, prevalent_wind: str
    ) -> int:
        """
        计算雀头符数

        Args:
            jantou_tile: 雀头的牌
            seat_wind: 自风
            prevalent_wind: 场风

        Returns:
            符数
        """
        if not jantou_tile.is_honor():
            return 0

        fu = 0

        # 三元牌雀头：2符
        if jantou_tile.is_dragon():
            fu = 2

        # 风牌雀头
        elif jantou_tile.is_wind():
            wind_map = {"E": 1, "S": 2, "W": 3, "N": 4}
            seat_wind_value = wind_map.get(seat_wind)
            prevalent_wind_value = wind_map.get(prevalent_wind)

            # 自风：2符
            if jantou_tile.value == seat_wind_value:
                fu = 2

            # 场风：2符
            if jantou_tile.value == prevalent_wind_value:
                fu = 2

            # 连风（既是自风又是场风）：4符
            if (
                jantou_tile.value == seat_wind_value
                and jantou_tile.value == prevalent_wind_value
            ):
                fu = 4

        return fu

    def _calculate_koutsu_fu(self, tile: Tile, is_anko: bool, is_terminal: bool) -> int:
        """
        计算刻子符数

        Args:
            tile: 刻子的牌
            is_anko: 是否暗刻
            is_terminal: 是否幺九牌

        Returns:
            符数
        """
        if is_anko:
            # 暗刻
            if is_terminal:
                return 8  # 幺九暗刻
            else:
                return 4  # 中张暗刻
        else:
            # 明刻
            if is_terminal:
                return 4  # 幺九明刻
            else:
                return 2  # 中张明刻

    def _calculate_wait_fu(self, pattern: MentsuPattern, win_tile: Tile) -> int:
        """
        计算听牌形式符数

        边张、坎张、单骑：2符
        两面：0符

        Args:
            pattern: 面子组合模式
            win_tile: 和牌

        Returns:
            符数
        """
        # 单骑听牌（雀头）
        if pattern.jantou and win_tile == pattern.jantou[0]:
            return 2

        # 检查顺子中的听牌形式
        for shuntsu in pattern.shuntsu:
            if win_tile in shuntsu:
                # 边张：123听3或789听7
                if (shuntsu[2] == win_tile and shuntsu[0].value == 1) or (
                    shuntsu[0] == win_tile and shuntsu[2].value == 9
                ):
                    return 2

                # 坎张：中间的牌
                if shuntsu[1] == win_tile:
                    return 2

                # 两面：0符
                return 0

        # 刻子（嵌张类似）
        return 0
