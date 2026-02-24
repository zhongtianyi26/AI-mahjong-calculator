"""
手牌解析模块 - 解析手牌为标准型、七对子型等
"""

from typing import List, Tuple, Optional, Set
from .tiles import Tile, parse_tiles_string
from collections import Counter


class MentsuPattern:
    """面子模式"""

    def __init__(
        self,
        shuntsu: List[Tuple[Tile, Tile, Tile]],
        koutsu: List[Tuple[Tile, Tile, Tile]],
        jantou: Optional[Tuple[Tile, Tile]] = None,
    ):
        """
        初始化面子模式

        Args:
            shuntsu: 顺子列表
            koutsu: 刻子列表（包括暗刻和明刻）
            jantou: 雀头（对子）
        """
        self.shuntsu = shuntsu  # 顺子
        self.koutsu = koutsu  # 刻子
        self.jantou = jantou  # 雀头

    def __repr__(self):
        return f"MentsuPattern(顺子={len(self.shuntsu)}, 刻子={len(self.koutsu)}, 雀头={self.jantou is not None})"


class HandParser:
    """
    手牌解析器

    支持解析：
    - 标准型（4面子1雀头）
    - 七对子型
    - 国士无双型（可选）
    """

    def __init__(self):
        pass

    def parse(
        self, hand: List[Tile], win_tile: Optional[Tile] = None
    ) -> List[MentsuPattern]:
        """
        解析手牌，返回所有可能的面子组合

        Args:
            hand: 手牌列表（13张，不含和牌）
            win_tile: 和牌（可选，如果提供则为14张完整手牌）

        Returns:
            所有可能的面子组合模式列表
        """
        # 如果提供了和牌，则将其加入手牌
        all_tiles = hand.copy()
        if win_tile:
            all_tiles.append(win_tile)

        # 检查是否是七对子
        if self.is_chiitoitsu(all_tiles):
            return [self._create_chiitoitsu_pattern(all_tiles)]

        # 检查是否是国士无双
        if self.is_kokushi(all_tiles):
            return [self._create_kokushi_pattern(all_tiles)]

        # 解析标准型
        patterns = self._parse_standard(all_tiles)

        return patterns

    def is_chiitoitsu(self, tiles: List[Tile]) -> bool:
        """
        判断是否是七对子

        Args:
            tiles: 14张牌

        Returns:
            是否是七对子
        """
        if len(tiles) != 14:
            return False

        tile_counts = Counter(tiles)

        # 必须是7个不同的对子
        if len(tile_counts) != 7:
            return False

        return all(count == 2 for count in tile_counts.values())

    def is_kokushi(self, tiles: List[Tile]) -> bool:
        """
        判断是否是国士无双

        国士无双：1m, 9m, 1p, 9p, 1s, 9s, 东南西北白发中 各一张，其中一张重复

        Args:
            tiles: 14张牌

        Returns:
            是否是国士无双
        """
        if len(tiles) != 14:
            return False

        # 定义幺九牌
        yaochuuhai = [
            Tile.from_string("1m"),
            Tile.from_string("9m"),
            Tile.from_string("1p"),
            Tile.from_string("9p"),
            Tile.from_string("1s"),
            Tile.from_string("9s"),
            Tile.from_string("1z"),
            Tile.from_string("2z"),
            Tile.from_string("3z"),
            Tile.from_string("4z"),
            Tile.from_string("5z"),
            Tile.from_string("6z"),
            Tile.from_string("7z"),
        ]

        tile_counts = Counter(tiles)

        # 检查是否包含所有13种幺九牌
        for yaochu in yaochuuhai:
            if yaochu not in tile_counts:
                return False

        # 检查是否有一张重复（2张）
        has_pair = any(count == 2 for count in tile_counts.values())
        if not has_pair:
            return False

        # 检查其他牌都只有1张
        counts = list(tile_counts.values())
        counts.sort()
        return counts == [1] * 12 + [2]

    def _create_chiitoitsu_pattern(self, tiles: List[Tile]) -> MentsuPattern:
        """创建七对子模式（特殊处理）"""
        return MentsuPattern(shuntsu=[], koutsu=[], jantou=None)

    def _create_kokushi_pattern(self, tiles: List[Tile]) -> MentsuPattern:
        """创建国士无双模式（特殊处理）"""
        return MentsuPattern(shuntsu=[], koutsu=[], jantou=None)

    def _parse_standard(self, tiles: List[Tile]) -> List[MentsuPattern]:
        """
        解析标准型（4面子1雀头）

        使用递归回溯算法找出所有可能的组合

        Args:
            tiles: 14张牌

        Returns:
            所有可能的标准型组合
        """
        if len(tiles) != 14:
            return []

        patterns = []
        tile_counts = Counter(tiles)

        # 尝试所有可能的雀头
        seen: Set[Tuple] = set()
        for tile, count in tile_counts.items():
            if count >= 2:
                # 选择这张牌作为雀头
                remaining = tile_counts.copy()
                remaining[tile] -= 2
                if remaining[tile] == 0:
                    del remaining[tile]

                # 递归查找所有合法的4个面子组合
                for shuntsu_list, koutsu_list in self._find_mentsu(
                    remaining, 4, [], []
                ):
                    # 去重：同一种拆分方式可能被多个雀头候选产生
                    key = (
                        tile,
                        tuple(sorted(shuntsu_list)),
                        tuple(sorted(koutsu_list)),
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    pattern = MentsuPattern(
                        shuntsu=shuntsu_list, koutsu=koutsu_list, jantou=(tile, tile)
                    )
                    patterns.append(pattern)

        return patterns

    def _find_mentsu(
        self,
        tile_counts: Counter,
        needed: int,
        shuntsu_list: List,
        koutsu_list: List,
    ) -> List[Tuple[List, List]]:
        """
        递归查找所有合法的面子组合

        Args:
            tile_counts: 剩余的牌
            needed: 还需要几个面子
            shuntsu_list: 当前已找到的顺子列表
            koutsu_list: 当前已找到的刻子列表

        Returns:
            所有合法组合的列表，每项为 (shuntsu_list, koutsu_list)
        """
        if needed == 0:
            if len(tile_counts) == 0:
                return [(shuntsu_list.copy(), koutsu_list.copy())]
            return []

        if len(tile_counts) == 0:
            return []

        results = []

        # 获取最小的牌，保证搜索顺序确定
        tile = min(tile_counts.keys())
        count = tile_counts[tile]

        # 尝试组成刻子
        if count >= 3:
            remaining = tile_counts.copy()
            remaining[tile] -= 3
            if remaining[tile] == 0:
                del remaining[tile]

            for combo in self._find_mentsu(
                remaining,
                needed - 1,
                shuntsu_list,
                koutsu_list + [(tile, tile, tile)],
            ):
                results.append(combo)

        # 尝试组成顺子（只对数牌有效）
        if not tile.is_honor() and tile.value <= 7:
            tile2 = Tile(tile.value + 1, tile.tile_type)
            tile3 = Tile(tile.value + 2, tile.tile_type)

            if tile2 in tile_counts and tile3 in tile_counts:
                remaining = tile_counts.copy()
                remaining[tile] -= 1
                remaining[tile2] -= 1
                remaining[tile3] -= 1

                if remaining[tile] == 0:
                    del remaining[tile]
                if remaining[tile2] == 0:
                    del remaining[tile2]
                if remaining[tile3] == 0:
                    del remaining[tile3]

                for combo in self._find_mentsu(
                    remaining,
                    needed - 1,
                    shuntsu_list + [(tile, tile2, tile3)],
                    koutsu_list,
                ):
                    results.append(combo)

        return results

    def is_tenpai(self, hand: List[Tile]) -> bool:
        """
        判断是否听牌

        Args:
            hand: 13张手牌

        Returns:
            是否听牌
        """
        if len(hand) != 13:
            return False

        # 尝试所有可能的牌
        all_possible_tiles = []
        for tile_type_str in ["m", "p", "s", "z"]:
            max_value = 7 if tile_type_str == "z" else 9
            for value in range(1, max_value + 1):
                all_possible_tiles.append(Tile.from_string(f"{value}{tile_type_str}"))

        # 检查是否可以和任何一张牌
        for tile in all_possible_tiles:
            test_hand = hand.copy()
            test_hand.append(tile)

            if len(self.parse(test_hand)) > 0:
                return True

        return False
