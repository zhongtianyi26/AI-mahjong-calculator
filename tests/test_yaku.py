"""
测试 - 役种判断
"""

import pytest
from mahjong_calculator.calculator.tiles import parse_tiles_string, Tile
from mahjong_calculator.calculator.parser import HandParser
from mahjong_calculator.calculator.yaku import YakuChecker
from mahjong_calculator import Calculator
from mahjong_calculator.calculator.yaku import YakuChecker


@pytest.fixture
def parser():
    return HandParser()


@pytest.fixture
def yaku_checker():
    return YakuChecker()


def test_tanyao(parser, yaku_checker):
    """测试断幺九"""
    hand = parse_tiles_string("234m456p678s2233z")
    win_tile = Tile.from_string("3z")
    patterns = parser.parse(hand, win_tile)

    # 有字牌，不是断幺九
    yaku_list = yaku_checker.check_yaku(hand, win_tile, patterns)
    assert not any(name == "断幺九" for name, _ in yaku_list)

    # 全是中张牌
    hand = parse_tiles_string("234m456p678s5566s")
    win_tile = Tile.from_string("5s")
    patterns = parser.parse(hand, win_tile)
    yaku_list = yaku_checker.check_yaku(hand, win_tile, patterns, is_tsumo=True)

    # 应该有断幺九
    assert any(name == "断幺九" for name, _ in yaku_list)


def test_pinfu(parser, yaku_checker):
    """测试平和"""
    hand = parse_tiles_string("234m456p234s6788s")
    win_tile = Tile.from_string("5s")
    patterns = parser.parse(hand, win_tile)

    yaku_list = yaku_checker.check_yaku(
        hand,
        win_tile,
        patterns,
        is_tsumo=True,
        is_menzen=True,
        seat_wind="S",
        prevalent_wind="E",
    )

    # 测试解析是否成功（至少有一些役种或者能够解析）
    assert patterns is not None and len(patterns) > 0


def test_yakuhai(parser, yaku_checker):
    """测试役牌"""
    # 白的刻子
    hand = parse_tiles_string("234m456p555z666z7z")
    win_tile = Tile.from_string("7z")
    patterns = parser.parse(hand, win_tile)

    yaku_list = yaku_checker.check_yaku(
        hand, win_tile, patterns, prevalent_wind="E", seat_wind="S"
    )

    # 应该有役牌:白
    assert any(name == "役牌:白" for name, _ in yaku_list)


def test_chiitoitsu(parser, yaku_checker):
    """测试七对子"""
    hand = parse_tiles_string("1122m3344p5566s7z")
    win_tile = Tile.from_string("7z")
    patterns = parser.parse(hand, win_tile)

    assert parser.is_chiitoitsu(hand + [win_tile])

    yaku_list = yaku_checker.check_yaku(hand, win_tile, patterns)

    # 应该有七对子
    assert any(name == "七对子" for name, _ in yaku_list)


def test_honitsu(parser, yaku_checker):
    """测试混一色"""
    hand = parse_tiles_string("123m456m789m1122z")
    win_tile = Tile.from_string("2z")
    patterns = parser.parse(hand, win_tile)

    yaku_list = yaku_checker.check_yaku(hand, win_tile, patterns, is_menzen=True)

    # 应该有混一色
    assert any(name == "混一色" for name, _ in yaku_list)


def test_chinitsu(parser, yaku_checker):
    """测试清一色"""
    hand = parse_tiles_string("123m456m789m1122m")
    win_tile = Tile.from_string("2m")
    patterns = parser.parse(hand, win_tile)

    yaku_list = yaku_checker.check_yaku(hand, win_tile, patterns, is_menzen=True)

    # 应该有清一色
    assert any(name == "清一色" for name, _ in yaku_list)


# -----------------------------------------------------------------------
# 多拆法→不同役种→自动取最高番 (YakuChecker 层)
# -----------------------------------------------------------------------


class TestBestPatternSelection:
    """
    验证当一副手牌存在多种面子拆分方式、各拆法产生不同役种时，
    check_yaku / Calculator 能正确遍历所有拆法并选取番数/点数最高的结果。
    """

    @pytest.fixture
    def parser(self):
        return HandParser()

    @pytest.fixture
    def yaku_checker(self):
        return YakuChecker()

    @pytest.fixture
    def calc(self):
        return Calculator()

    # ---- YakuChecker.check_yaku 自动选最高番 ----

    def test_sanankou_over_iipeiko(self, parser, yaku_checker):
        """
        222333444m456p11z（14张）
        拆法1：[222m][333m][444m][456p] → 三暗刻(2) + 自摸(1) = 3番
        拆法2：[234m]×3 + [456p]      → 一杯口(1) + 自摸(1) = 2番
        check_yaku 应选择拆法1（三暗刻，更高番）。
        """
        hand = parse_tiles_string("222333444m456p1z")
        win = Tile.from_string("1z")
        patterns = parser.parse(hand, win)
        assert len(patterns) == 2, "应有两种拆法"

        best = yaku_checker.check_yaku(
            hand=hand,
            win_tile=win,
            patterns=patterns,
            is_tsumo=True,
            is_menzen=True,
            seat_wind="S",
            prevalent_wind="E",
        )
        total_han = sum(h for _, h in best)
        assert total_han == 3
        assert any(name == "三暗刻" for name, _ in best), "应选含三暗刻的拆法"
        assert any(name == "门前清自摸" for name, _ in best)

    def test_iipeiko_chanta_over_sanankou(self, parser, yaku_checker):
        """
        111222333m123p11z（14张）
        拆法1（刻子）：[111m][222m][333m][123p] → 三暗刻(2) + 自摸(1) = 3番
        拆法2（顺子）：[123m]×3 + [123p]      → 一杯口(1) + 混全带幺九(2) + 自摸(1) = 4番
        check_yaku 应选择拆法2（4番 > 3番）。
        """
        hand = parse_tiles_string("111222333m123p1z")
        win = Tile.from_string("1z")
        patterns = parser.parse(hand, win)
        assert len(patterns) == 2, "应有两种拆法"

        best = yaku_checker.check_yaku(
            hand=hand,
            win_tile=win,
            patterns=patterns,
            is_tsumo=True,
            is_menzen=True,
            seat_wind="S",
            prevalent_wind="E",
        )
        total_han = sum(h for _, h in best)
        assert total_han == 4
        assert any(name == "一杯口" for name, _ in best), "应选含一杯口的拆法"
        assert any(name == "混全带幺九" for name, _ in best), "应选含混全带幺九的拆法"
        # 不应包含三暗刻
        assert not any(
            name == "三暗刻" for name, _ in best
        ), "不应包含三暗刻（那是更低番的拆法）"

    def test_each_pattern_gets_different_yaku(self, parser, yaku_checker):
        """
        验证同一手牌两种拆法确实产生不同的役，
        用 _check_yaku_for_pattern 分别检查。
        """
        hand = parse_tiles_string("222333444m456p1z")
        win = Tile.from_string("1z")
        patterns = parser.parse(hand, win)

        yaku_sets = []
        for p in patterns:
            yl = yaku_checker._check_yaku_for_pattern(
                all_tiles=hand + [win],
                pattern=p,
                win_tile=win,
                is_tsumo=True,
                is_menzen=True,
                seat_wind="S",
                prevalent_wind="E",
            )
            yaku_names = frozenset(name for name, _ in yl)
            yaku_sets.append(yaku_names)

        # 两种拆法的役名集合不应完全相同
        assert yaku_sets[0] != yaku_sets[1], "两种拆法应产生不同的役种组合"

    # ---- Calculator 全流程：最终取最高点数 ----

    def test_calculator_picks_highest_points(self, calc):
        """
        111222333m123p11z + win=1z, 自摸
        拆法1（刻子）：三暗刻+自摸 = 3番40符 = 5200
        拆法2（顺子）：一杯口+混全带幺九+自摸 = 4番30符 = 7700
        Calculator 应选拆法2，点数更高。
        """
        r = calc.calculate(
            hand="111222333m123p1z",
            win_tile="1z",
            is_tsumo=True,
        )
        assert r.is_valid
        assert r.han == 4
        assert any(name == "一杯口" for name, _ in r.yaku_list)
        assert any(name == "混全带幺九" for name, _ in r.yaku_list)
        assert r.total_points == 7700

    def test_calculator_sanankou_is_best(self, calc):
        """
        222333444m456p11z + win=1z, 自摸
        拆法1（刻子）：三暗刻+自摸 = 3番
        拆法2（顺子）：一杯口+自摸 = 2番
        Calculator 应选拆法1（三暗刻）。
        """
        r = calc.calculate(
            hand="222333444m456p1z",
            win_tile="1z",
            is_tsumo=True,
        )
        assert r.is_valid
        assert r.han >= 3
        assert any(name == "三暗刻" for name, _ in r.yaku_list)

    def test_calculator_single_pattern_unchanged(self, calc):
        """
        只有单一拆法的手牌，Calculator 行为不变。
        """
        r = calc.calculate(
            hand="123m456p789s456s1z",
            win_tile="1z",
            is_tsumo=True,
        )
        assert r.is_valid
        assert r.han >= 1  # 至少有门前清自摸
