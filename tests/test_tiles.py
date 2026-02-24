"""
测试 - 牌的数据结构
"""

import pytest
from mahjong_calculator.calculator.tiles import (
    Tile,
    TileType,
    parse_tiles_string,
    tiles_to_string,
)


def test_tile_creation():
    """测试牌的创建"""
    tile = Tile(1, TileType.MANZU)
    assert tile.value == 1
    assert tile.tile_type == TileType.MANZU
    assert tile.to_string() == "1m"


def test_tile_from_string():
    """测试从字符串创建牌"""
    tile = Tile.from_string("5p")
    assert tile.value == 5
    assert tile.tile_type == TileType.PINZU


def test_tile_properties():
    """测试牌的属性判断"""
    # 幺九牌
    assert Tile.from_string("1m").is_terminal() == True
    assert Tile.from_string("9s").is_terminal() == True
    assert Tile.from_string("5m").is_terminal() == False
    assert Tile.from_string("1z").is_terminal() == True

    # 中张牌
    assert Tile.from_string("2m").is_simple() == True
    assert Tile.from_string("8s").is_simple() == True
    assert Tile.from_string("1m").is_simple() == False
    assert Tile.from_string("1z").is_simple() == False

    # 字牌
    assert Tile.from_string("1z").is_honor() == True
    assert Tile.from_string("7z").is_honor() == True
    assert Tile.from_string("5m").is_honor() == False

    # 风牌
    assert Tile.from_string("1z").is_wind() == True
    assert Tile.from_string("4z").is_wind() == True
    assert Tile.from_string("5z").is_wind() == False

    # 三元牌
    assert Tile.from_string("5z").is_dragon() == True
    assert Tile.from_string("7z").is_dragon() == True
    assert Tile.from_string("4z").is_dragon() == False


def test_parse_tiles_string():
    """测试解析牌字符串"""
    # 紧凑格式
    tiles = parse_tiles_string("123m456p789s11z")
    assert len(tiles) == 11
    assert tiles[0].to_string() == "1m"
    assert tiles[3].to_string() == "4p"
    assert tiles[-1].to_string() == "1z"

    # 混合格式（国士无双）
    tiles = parse_tiles_string("19m19p19s1234567z")
    assert len(tiles) == 13


def test_tiles_to_string():
    """测试将牌列表转换为字符串"""
    tiles = [
        Tile.from_string("1m"),
        Tile.from_string("2m"),
        Tile.from_string("3m"),
        Tile.from_string("4p"),
        Tile.from_string("5p"),
        Tile.from_string("6p"),
    ]
    result = tiles_to_string(tiles)
    assert result == "123m456p"
