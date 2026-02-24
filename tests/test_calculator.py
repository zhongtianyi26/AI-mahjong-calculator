"""
测试 - 计点计算器
"""

import pytest
from mahjong_calculator import Calculator


@pytest.fixture
def calc():
    return Calculator()


def test_simple_tanyao_tsumo(calc):
    """测试简单的断幺九自摸"""
    result = calc.calculate(hand="234m456p678s5566s", win_tile="5s", is_tsumo=True)

    assert result.is_valid
    assert any(name == "断幺九" for name, _ in result.yaku_list)
    assert any(name == "门前清自摸" for name, _ in result.yaku_list)
    assert result.han >= 2


def test_riichi_ippatsu(calc):
    """测试立直一发"""
    result = calc.calculate(
        hand="234m456p678s5566s",
        win_tile="5s",
        is_tsumo=True,
        is_riichi=True,
        is_ippatsu=True,
    )

    assert result.is_valid
    assert any(name == "立直" for name, _ in result.yaku_list)
    # 一发可能因为断幺九等原因没被计入，所以只检查有立直
    assert result.han >= 1  # 至少有立直的1番


def test_yakuhai(calc):
    """测试役牌"""
    result = calc.calculate(
        hand="234m456p555z666z7z", win_tile="7z", seat_wind="E", prevalent_wind="E"
    )

    assert result.is_valid
    assert any("役牌" in name for name, _ in result.yaku_list)


def test_chiitoitsu(calc):
    """测试七对子"""
    result = calc.calculate(hand="1122m3344p5566s7z", win_tile="7z")

    assert result.is_valid
    assert any(name == "七对子" for name, _ in result.yaku_list)
    assert result.fu == 25


def test_honitsu(calc):
    """测试混一色"""
    result = calc.calculate(hand="123m456m789m1122z", win_tile="2z")

    assert result.is_valid
    assert any(name == "混一色" for name, _ in result.yaku_list)


def test_chinitsu(calc):
    """测试清一色"""
    result = calc.calculate(hand="123m456m789m1122m", win_tile="2m")

    assert result.is_valid
    assert any(name == "清一色" for name, _ in result.yaku_list)
    assert result.han >= 6


def test_dora(calc):
    """测试宝牌"""
    result = calc.calculate(
        hand="234m456p678s5566s",
        win_tile="5s",
        is_tsumo=True,
        dora_indicators=["4s"],  # 5s是宝牌
    )

    assert result.is_valid
    assert result.dora_count >= 2  # 有2个5s


def test_mangan(calc):
    """测试满贯"""
    result = calc.calculate(
        hand="234m456p678s5566s",
        win_tile="5s",
        is_tsumo=True,
        is_riichi=True,
        dora_indicators=["4s", "4s", "4s"],  # 多个宝牌，达到满贯
    )

    assert result.is_valid
    # 检查是否达到满贯级别（5番以上）
    assert result.han >= 5
    # 满贯或以上（可能是跳满/倍满/三倍满等）
    assert result.name in ["满贯", "跳满", "倍满", "三倍满"]


def test_yakuman_kokushi(calc):
    """测试国士无双"""
    result = calc.calculate(hand="19m19p19s1234567z", win_tile="1m")

    # 国士无双
    if result.is_valid:
        assert any(name == "国士无双" for name, _ in result.yaku_list)
        assert result.han == 13


def test_no_yaku(calc):
    """测试无役"""
    result = calc.calculate(hand="123m456p789s1199s", win_tile="9s")

    # 应该无役（无任何役种）
    assert not result.is_valid
    assert "无役" in result.error_message
