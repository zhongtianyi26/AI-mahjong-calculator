"""
麻将牌的数据结构定义
"""

from enum import Enum
from typing import List, Optional


class TileType(Enum):
    """牌的类型"""

    MANZU = "m"  # 万子
    PINZU = "p"  # 筒子
    SOUZU = "s"  # 索子
    JIHAI = "z"  # 字牌


class Tile:
    """
    麻将牌类

    表示方式：数字+类型
    - 1-9m: 一至九万
    - 1-9p: 一至九筒
    - 1-9s: 一至九索
    - 1-7z: 东南西北白发中
    """

    def __init__(self, value: int, tile_type: TileType):
        """
        初始化麻将牌

        Args:
            value: 牌的数值 (1-9 for 数牌, 1-7 for 字牌)
            tile_type: 牌的类型
        """
        self.value = value
        self.tile_type = tile_type

        # 验证合法性
        if tile_type in [TileType.MANZU, TileType.PINZU, TileType.SOUZU]:
            if not 1 <= value <= 9:
                raise ValueError(f"数牌的值必须在1-9之间: {value}")
        elif tile_type == TileType.JIHAI:
            if not 1 <= value <= 7:
                raise ValueError(f"字牌的值必须在1-7之间: {value}")

    @classmethod
    def from_string(cls, tile_str: str) -> "Tile":
        """
        从字符串创建牌

        Args:
            tile_str: 牌的字符串表示，如 "1m", "5p", "7z"

        Returns:
            Tile对象
        """
        if len(tile_str) != 2:
            raise ValueError(f"无效的牌表示: {tile_str}")

        value = int(tile_str[0])
        type_char = tile_str[1]

        tile_type = TileType(type_char)
        return cls(value, tile_type)

    def to_string(self) -> str:
        """转换为字符串表示"""
        return f"{self.value}{self.tile_type.value}"

    def is_terminal(self) -> bool:
        """是否是幺九牌（1或9的数牌，或字牌）"""
        if self.tile_type == TileType.JIHAI:
            return True
        return self.value in [1, 9]

    def is_honor(self) -> bool:
        """是否是字牌"""
        return self.tile_type == TileType.JIHAI

    def is_simple(self) -> bool:
        """是否是中张牌（2-8）"""
        if self.tile_type == TileType.JIHAI:
            return False
        return 2 <= self.value <= 8

    def is_wind(self) -> bool:
        """是否是风牌（东南西北）"""
        return self.tile_type == TileType.JIHAI and 1 <= self.value <= 4

    def is_dragon(self) -> bool:
        """是否是三元牌（白发中）"""
        return self.tile_type == TileType.JIHAI and 5 <= self.value <= 7

    def next_tile(self) -> Optional["Tile"]:
        """获取下一张牌（用于顺子判断）"""
        if self.tile_type == TileType.JIHAI:
            return None
        if self.value == 9:
            return None
        return Tile(self.value + 1, self.tile_type)

    def prev_tile(self) -> Optional["Tile"]:
        """获取上一张牌"""
        if self.tile_type == TileType.JIHAI:
            return None
        if self.value == 1:
            return None
        return Tile(self.value - 1, self.tile_type)

    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return self.value == other.value and self.tile_type == other.tile_type

    def __hash__(self):
        return hash((self.value, self.tile_type))

    def __lt__(self, other):
        """用于排序"""
        if not isinstance(other, Tile):
            return NotImplemented

        # 按类型顺序：万 < 筒 < 索 < 字
        type_order = {
            TileType.MANZU: 0,
            TileType.PINZU: 1,
            TileType.SOUZU: 2,
            TileType.JIHAI: 3,
        }

        if self.tile_type != other.tile_type:
            return type_order[self.tile_type] < type_order[other.tile_type]
        return self.value < other.value

    def __repr__(self):
        return f"Tile({self.to_string()})"

    def __str__(self):
        return self.to_string()


class MeldType(Enum):
    """面子类型"""

    CHI = "chi"  # 吃（顺子）
    PON = "pon"  # 碰（刻子）
    KAN = "kan"  # 杠
    ANKAN = "ankan"  # 暗杠


class Meld:
    """
    面子（副露）
    """

    def __init__(self, meld_type: MeldType, tiles: List[Tile]):
        """
        初始化面子

        Args:
            meld_type: 面子类型
            tiles: 组成面子的牌
        """
        self.meld_type = meld_type
        self.tiles = sorted(tiles)

    def is_open(self) -> bool:
        """是否是明面子（除暗杠外都是明面子）"""
        return self.meld_type != MeldType.ANKAN

    def __repr__(self):
        tiles_str = "".join(str(t) for t in self.tiles)
        return f"Meld({self.meld_type.value}: {tiles_str})"


def parse_tiles_string(tiles_str: str) -> List[Tile]:
    """
    解析牌的字符串表示

    支持格式：
    - "123m456p789s" - 紧凑格式
    - "1m2m3m4p5p6p" - 完整格式

    Args:
        tiles_str: 牌的字符串表示

    Returns:
        Tile对象列表
    """
    tiles = []
    current_numbers = []

    i = 0
    while i < len(tiles_str):
        char = tiles_str[i]

        if char.isdigit():
            current_numbers.append(int(char))
        elif char in ["m", "p", "s", "z"]:
            tile_type = TileType(char)
            for num in current_numbers:
                tiles.append(Tile(num, tile_type))
            current_numbers = []
        else:
            raise ValueError(f"无效字符: {char}")

        i += 1

    if current_numbers:
        raise ValueError(f"数字后缺少类型标识: {current_numbers}")

    return tiles


def tiles_to_string(tiles: List[Tile]) -> str:
    """
    将牌列表转换为紧凑字符串格式

    Args:
        tiles: Tile对象列表

    Returns:
        字符串表示，如 "123m456p789s"
    """
    # 按类型分组
    groups = {
        TileType.MANZU: [],
        TileType.PINZU: [],
        TileType.SOUZU: [],
        TileType.JIHAI: [],
    }

    for tile in sorted(tiles):
        groups[tile.tile_type].append(tile.value)

    # 组合成字符串
    result = ""
    for tile_type in [TileType.MANZU, TileType.PINZU, TileType.SOUZU, TileType.JIHAI]:
        if groups[tile_type]:
            values_str = "".join(str(v) for v in sorted(groups[tile_type]))
            result += values_str + tile_type.value

    return result
