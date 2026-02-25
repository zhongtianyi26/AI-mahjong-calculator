"""
手牌解析模块 - 解析手牌为标准型、七对子型等
"""

from typing import List, Tuple, Optional, Set
from .tiles import Tile, Meld, MeldType, parse_tiles_string
from collections import Counter


class MentsuPattern:
    """面子模式

    所有面子（暗+明+杠）统一存储，同时分别标记暗/明便于役种和符数判断。
    """

    def __init__(
        self,
        shuntsu: List[Tuple[Tile, Tile, Tile]] = None,
        koutsu: List[Tuple[Tile, Tile, Tile]] = None,
        jantou: Optional[Tuple[Tile, Tile]] = None,
        open_shuntsu: List[Tuple[Tile, Tile, Tile]] = None,
        open_koutsu: List[Tuple[Tile, Tile, Tile]] = None,
        min_kantsu: List[Tuple[Tile, ...]] = None,
        ankan: List[Tuple[Tile, ...]] = None,
    ):
        """
        Args:
            shuntsu: 暗顺子（门前手牌拆出的）
            koutsu:  暗刻子（门前手牌拆出的）
            jantou:  雀头
            open_shuntsu: 明顺子（吃）
            open_koutsu:  明刻子（碰）
            min_kantsu:   明杠（大明杠 / 加杠）
            ankan:        暗杠
        """
        self.shuntsu = shuntsu or []  # 暗顺
        self.koutsu = koutsu or []  # 暗刻
        self.jantou = jantou  # 雀头
        self.open_shuntsu = open_shuntsu or []  # 明顺
        self.open_koutsu = open_koutsu or []  # 明刻
        self.min_kantsu = min_kantsu or []  # 明杠
        self.ankan = ankan or []  # 暗杠

    # ---- 便捷属性 ----
    @property
    def all_shuntsu(self) -> List[Tuple[Tile, Tile, Tile]]:
        """所有顺子（暗+明）"""
        return self.shuntsu + self.open_shuntsu

    @property
    def all_koutsu(self) -> List[Tuple[Tile, Tile, Tile]]:
        """所有刻子（暗+明，不含杠）"""
        return self.koutsu + self.open_koutsu

    @property
    def all_koutsu_and_kantsu(self) -> list:
        """所有刻/杠（暗刻+明刻+明杠+暗杠）"""
        return self.koutsu + self.open_koutsu + self.min_kantsu + self.ankan

    @property
    def mentsu_count(self) -> int:
        """面子总数"""
        return (
            len(self.shuntsu)
            + len(self.koutsu)
            + len(self.open_shuntsu)
            + len(self.open_koutsu)
            + len(self.min_kantsu)
            + len(self.ankan)
        )

    @property
    def kan_count(self) -> int:
        """杠子总数"""
        return len(self.min_kantsu) + len(self.ankan)

    def __repr__(self):
        return (
            f"MentsuPattern(暗顺={len(self.shuntsu)}, 暗刻={len(self.koutsu)}, "
            f"明顺={len(self.open_shuntsu)}, 明刻={len(self.open_koutsu)}, "
            f"明杠={len(self.min_kantsu)}, 暗杠={len(self.ankan)}, "
            f"雀头={self.jantou is not None})"
        )


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
        self,
        hand: List[Tile],
        win_tile: Optional[Tile] = None,
        melds: List[Meld] = None,
    ) -> List[MentsuPattern]:
        """
        解析手牌，返回所有可能的面子组合

        Args:
            hand: 手牌列表（门前牌，含和牌时13张，有副露时更少）
            win_tile: 和牌（可选，如果提供则加入门前牌一起拆）
            melds: 已声明的副露列表

        Returns:
            所有可能的面子组合模式列表
        """
        # 门前部分的牌
        closed_tiles = hand.copy()
        if win_tile:
            closed_tiles.append(win_tile)

        # 将副露转为 pattern 字段
        open_shuntsu: List[Tuple[Tile, Tile, Tile]] = []
        open_koutsu: List[Tuple[Tile, Tile, Tile]] = []
        min_kantsu: List[Tuple[Tile, ...]] = []
        ankan_list: List[Tuple[Tile, ...]] = []

        if melds:
            for m in melds:
                ts = tuple(sorted(m.tiles))
                if m.meld_type == MeldType.CHI:
                    open_shuntsu.append(ts[:3])
                elif m.meld_type == MeldType.PON:
                    open_koutsu.append(ts[:3])
                elif m.meld_type == MeldType.KAN:
                    min_kantsu.append(ts)
                elif m.meld_type == MeldType.ANKAN:
                    ankan_list.append(ts)

        n_closed = len(closed_tiles)
        # 副露后门前牌张数: 14 - 3*chi/pon - 4*kan/ankan
        meld_open = (
            len(open_shuntsu) + len(open_koutsu) + len(min_kantsu) + len(ankan_list)
        )

        # 全部14张用于七对子/国士判断（仅门前时有效）
        if not melds:
            all_tiles_flat = closed_tiles
            if self.is_chiitoitsu(all_tiles_flat):
                return [MentsuPattern(jantou=None)]  # 七对子特殊 pattern

            if self.is_kokushi(all_tiles_flat):
                return [MentsuPattern(jantou=None)]  # 国士特殊 pattern

        # 门前部分需要拆的面子数
        needed = 4 - meld_open
        if needed < 0:
            return []

        # 对门前牌做标准拆解
        patterns = self._parse_standard_flexible(closed_tiles, needed)

        # 将副露面子注入每个 pattern
        result = []
        for pat in patterns:
            pat.open_shuntsu = list(open_shuntsu)
            pat.open_koutsu = list(open_koutsu)
            pat.min_kantsu = list(min_kantsu)
            pat.ankan = list(ankan_list)
            result.append(pat)

        return result

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

    def _parse_standard_flexible(
        self, tiles: List[Tile], needed: int
    ) -> List[MentsuPattern]:
        """
        解析标准型（needed个面子 + 1雀头）

        Args:
            tiles: 门前部分的牌
            needed: 需要从中拆出的面子数

        Returns:
            所有可能的标准型组合
        """
        expected = needed * 3 + 2
        if len(tiles) != expected:
            return []

        patterns = []
        tile_counts = Counter(tiles)

        seen: Set[Tuple] = set()
        for tile, count in tile_counts.items():
            if count >= 2:
                remaining = tile_counts.copy()
                remaining[tile] -= 2
                if remaining[tile] == 0:
                    del remaining[tile]

                for shuntsu_list, koutsu_list in self._find_mentsu(
                    remaining, needed, [], []
                ):
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

    # 保留旧方法名兼容
    def _parse_standard(self, tiles: List[Tile]) -> List[MentsuPattern]:
        return self._parse_standard_flexible(tiles, 4)

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
