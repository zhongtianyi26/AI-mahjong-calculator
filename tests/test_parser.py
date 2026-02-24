"""
测试 - 手牌解析器
"""

import pytest
from mahjong_calculator.calculator.tiles import Tile, parse_tiles_string
from mahjong_calculator.calculator.parser import HandParser, MentsuPattern


@pytest.fixture
def parser():
    return HandParser()


# -----------------------------------------------------------------------
# 辅助函数
# -----------------------------------------------------------------------


def sorted_mentsu_key(pattern: MentsuPattern):
    """将一个 MentsuPattern 转为可比较的 frozenset，用于去重断言"""
    shuntsu = frozenset(tuple(t.to_string() for t in m) for m in pattern.shuntsu)
    koutsu = frozenset(tuple(t.to_string() for t in m) for m in pattern.koutsu)
    jantou = pattern.jantou[0].to_string() if pattern.jantou else None
    return (jantou, shuntsu, koutsu)


# -----------------------------------------------------------------------
# is_chiitoitsu
# -----------------------------------------------------------------------


class TestIsChiitoitsu:
    def test_valid_chiitoitsu(self, parser):
        """7 个不同对子 → 七对子（14 张）"""
        tiles = parse_tiles_string("11223344556677m")  # 7 对，共 14 张
        assert parser.is_chiitoitsu(tiles) is True

    def test_valid_chiitoitsu_mixed(self, parser):
        """跨花色七对子（14 张）"""
        # 1z×2, 2z×2, 3z×2, 4z×2 + 1m×2, 2p×2, 3s×2 = 14 张，7 个不同对子
        tiles = parse_tiles_string("11m22p33s11223344z")
        assert parser.is_chiitoitsu(tiles) is True

    def test_not_chiitoitsu_has_triple(self, parser):
        """含刻子（3张同牌）→ 不是七对子"""
        tiles = parse_tiles_string("1112334455667m")
        assert parser.is_chiitoitsu(tiles) is False

    def test_not_chiitoitsu_wrong_count(self, parser):
        """不是14张 → 不是七对子"""
        tiles = parse_tiles_string("112233445566m")  # 13 张
        assert parser.is_chiitoitsu(tiles) is False

    def test_not_chiitoitsu_duplicate_pair(self, parser):
        """同一对子出现2次（即4张同牌）→ 不是七对子"""
        tiles = parse_tiles_string("1111334455667m")
        assert parser.is_chiitoitsu(tiles) is False


# -----------------------------------------------------------------------
# is_kokushi
# -----------------------------------------------------------------------


class TestIsKokushi:
    def test_valid_kokushi(self, parser):
        """标准国士无双（1m重复）"""
        tiles = parse_tiles_string("19m19p19s1234567z")
        # 用额外的 1m 替换使其中一张重复：共14张
        # 19m19p19s1234567z = 2+2+2+7=13；再加1m变成正确14张
        hand14 = parse_tiles_string("119m9p19s1234567z")
        # 重新手工构造：确保13种幺九各1张，其中1张重复
        from mahjong_calculator.calculator.tiles import Tile

        tiles = [
            Tile.from_string(s)
            for s in [
                "1m",
                "1m",
                "9m",
                "1p",
                "9p",
                "1s",
                "9s",
                "1z",
                "2z",
                "3z",
                "4z",
                "5z",
                "6z",
                "7z",
            ]
        ]
        assert parser.is_kokushi(tiles) is True

    def test_not_kokushi_missing_tile(self, parser):
        """缺少一种幺九牌 → 不是国士无双"""
        # 用 2m 代替 9m
        tiles = [
            Tile.from_string(s)
            for s in [
                "1m",
                "1m",
                "2m",
                "1p",
                "9p",
                "1s",
                "9s",
                "1z",
                "2z",
                "3z",
                "4z",
                "5z",
                "6z",
                "7z",
            ]
        ]
        assert parser.is_kokushi(tiles) is False

    def test_not_kokushi_no_pair(self, parser):
        """13种幺九牌各1张但无对子 → 不是国士无双"""
        tiles = [
            Tile.from_string(s)
            for s in [
                "1m",
                "9m",
                "1p",
                "9p",
                "1s",
                "9s",
                "1z",
                "2z",
                "3z",
                "4z",
                "5z",
                "6z",
                "7z",
                "5m",
            ]
        ]
        assert parser.is_kokushi(tiles) is False


# -----------------------------------------------------------------------
# _parse_standard / parse — 单一解析结果
# -----------------------------------------------------------------------


class TestParseStandardSingle:
    def test_simple_hand_one_pattern(self, parser):
        """简单无歧义手牌 → 恰好1种解析"""
        # [123m][456p][789s][45s] + 雀头 11z  共 13+1=14 张
        # hand13 = 123m456p789s45s11z（13 张），win_tile = 6s 补完 [456s]
        hand13 = parse_tiles_string("123m456p789s45s11z")  # 3+3+3+2+2=13
        win_tile = Tile.from_string("6s")
        patterns = parser.parse(hand13, win_tile)
        assert len(patterns) == 1

        p = patterns[0]
        assert p.jantou is not None
        assert p.jantou[0].to_string() == "1z"
        assert len(p.shuntsu) == 4
        assert len(p.koutsu) == 0

    def test_koutsu_hand(self, parser):
        """全刻子手牌（三暗刻 + 1顺子）"""
        # [111m][222p][333s][456s] + 雀头 1z×2  共 13+1=14 张
        # hand13 = 111m222p333s456s1z（13 张），win_tile = 1z 补完雀头
        hand13 = parse_tiles_string("111m222p333s456s1z")  # 3+3+3+3+1=13
        win_tile = Tile.from_string("1z")
        patterns = parser.parse(hand13, win_tile)
        assert len(patterns) == 1

        p = patterns[0]
        assert p.jantou[0].to_string() == "1z"
        assert len(p.koutsu) == 3
        assert len(p.shuntsu) == 1

    def test_not_winning_hand_empty(self, parser):
        """非和牌手型 → 空列表"""
        hand13 = parse_tiles_string("123m456p789s12z")
        win_tile = Tile.from_string("3z")
        patterns = parser.parse(hand13, win_tile)
        assert len(patterns) == 0


# -----------------------------------------------------------------------
# 多种解析结果（核心：验证穷举修复）
# -----------------------------------------------------------------------


class TestParseMultiplePatterns:
    def test_sanshoku_ambiguous_splits(self, parser):
        """
        111222333m456p11z —— 同一副牌存在两种面子拆分方式
        拆法1: [123m][123m][123m][456p]  (3顺子+1顺子)
        拆法2: [111m][222m][333m][456p]  (3刻子+1顺子)
        修复前只返回1种，修复后应返回2种。
        """
        hand13 = parse_tiles_string("111222333m456p1z")
        win_tile = Tile.from_string("1z")
        patterns = parser.parse(hand13, win_tile)

        assert len(patterns) == 2, (
            f"期望2种解析，实际得到{len(patterns)}种："
            f"\n{[sorted_mentsu_key(p) for p in patterns]}"
        )

        keys = {sorted_mentsu_key(p) for p in patterns}
        # 拆法1：3顺子
        shuntsu_key = frozenset(
            {
                ("1m", "2m", "3m"),
                ("1m", "2m", "3m"),
                ("1m", "2m", "3m"),
                ("4p", "5p", "6p"),
            }
        )
        # 拆法2：3刻子
        koutsu_key = frozenset(
            {
                ("1m", "1m", "1m"),
                ("2m", "2m", "2m"),
                ("3m", "3m", "3m"),
                ("4p", "5p", "6p"),
            }
        )
        found_shuntsu = any(
            len(p.shuntsu) == 4 and len(p.koutsu) == 0 for p in patterns
        )
        found_koutsu = any(len(p.koutsu) == 3 and len(p.shuntsu) == 1 for p in patterns)
        assert found_shuntsu, "应有一种全顺子的拆法（3×[123m]+[456p]）"
        assert found_koutsu, "应有一种含3刻子的拆法（[111m][222m][333m]+[456p]）"

    def test_iipeiko_two_patterns(self, parser):
        """
        一盃口手牌：112233m456p789s11z
        雀头 1z，面子里 [123m][123m][456p][789s] 是唯一拆法 → 1种
        但要确认 parse 确实返回了包含两个相同顺子的那种拆法。
        """
        hand13 = parse_tiles_string("112233m456p789s1z")
        win_tile = Tile.from_string("1z")
        patterns = parser.parse(hand13, win_tile)

        assert len(patterns) >= 1
        # 必须存在含2个 (1m,2m,3m) 顺子的解析
        has_iipeiko_split = any(
            sum(
                1
                for s in p.shuntsu
                if s[0].to_string() == "1m" and s[1].to_string() == "2m"
            )
            == 2
            for p in patterns
        )
        assert has_iipeiko_split, "应存在一盃口顺子拆法 [123m][123m][456p][789s]"

    def test_all_patterns_are_valid(self, parser):
        """每种解析结果都应满足 4面子1雀头"""
        hand13 = parse_tiles_string("111222333m456p1z")
        win_tile = Tile.from_string("1z")
        patterns = parser.parse(hand13, win_tile)

        for p in patterns:
            assert p.jantou is not None, "每个pattern必须有雀头"
            assert len(p.shuntsu) + len(p.koutsu) == 4, "面子总数必须为4"

    def test_no_duplicate_patterns(self, parser):
        """不同解析结果之间不应有重复"""
        hand13 = parse_tiles_string("111222333m456p1z")
        win_tile = Tile.from_string("1z")
        patterns = parser.parse(hand13, win_tile)

        keys = [sorted_mentsu_key(p) for p in patterns]
        assert len(keys) == len(set(keys)), "解析结果中存在重复项"


# -----------------------------------------------------------------------
# 七对子 / 国士无双通过 parse 接口
# -----------------------------------------------------------------------


class TestParseSpecialHands:
    def test_parse_chiitoitsu(self, parser):
        """七对子手牌 → parse 返回1种且为七对子标记"""
        # hand13（13 张）+ win_tile（第 7 对的第 2 张）= 14 张七对子
        hand13 = parse_tiles_string("1122334455667m")  # 13 张
        win_tile = Tile.from_string("7m")  # 补全第 7 对
        patterns = parser.parse(hand13, win_tile)
        assert len(patterns) == 1
        # 七对子 pattern shuntsu/koutsu 均为空（特殊标记）
        p = patterns[0]
        assert p.shuntsu == []
        assert p.koutsu == []

    def test_parse_kokushi(self, parser):
        """国士无双 → parse 返回1种"""
        tiles_14 = [
            Tile.from_string(s)
            for s in [
                "1m",
                "1m",
                "9m",
                "1p",
                "9p",
                "1s",
                "9s",
                "1z",
                "2z",
                "3z",
                "4z",
                "5z",
                "6z",
                "7z",
            ]
        ]
        patterns = parser.parse(tiles_14)
        assert len(patterns) == 1
        p = patterns[0]
        assert p.shuntsu == []
        assert p.koutsu == []


# -----------------------------------------------------------------------
# is_tenpai
# -----------------------------------------------------------------------


class TestIsTenpai:
    def test_tenpai_tanki(self, parser):
        """单骑听牌：123m456p789s123s + 等 1z（雀头缺）→ 听牌"""
        hand13 = parse_tiles_string("123m456p789s123s1z")
        # "123m456p789s123s1z" = 3+3+3+3+1 = 13 张，等 1z 再来一张自摸
        # 实际等的是任意能配成对子的牌，这里 1z 只有1张，等第二张 1z
        assert parser.is_tenpai(hand13) is True

    def test_tenpai_sequential(self, parser):
        """两面听牌：123m456p789s11z + 缺一张顺子 → 听 2s 或 5s"""
        hand13 = parse_tiles_string("123m456p789s11z3s")
        # 3+3+3+2+1=12，不对；重新来
        # 123m456p11z + 789s 凑3+3+2+3=11...
        # 用 "456m789m123p456p1z" = 3+3+3+3+1=13 等 1z
        hand13 = parse_tiles_string("456m789m123p456p1z")
        assert parser.is_tenpai(hand13) is True

    def test_not_tenpai(self, parser):
        """孤立散牌，无法听牌"""
        # 246m246p246s1357z = 3+3+3+4=13，全是隔断牌和孤立字牌
        hand13 = parse_tiles_string("246m246p246s1357z")
        assert parser.is_tenpai(hand13) is False

    def test_tenpai_wrong_tile_count(self, parser):
        """非13张手牌 → is_tenpai 返回 False"""
        hand12 = parse_tiles_string("123m456p789s11z")  # 12 张
        assert parser.is_tenpai(hand12) is False


# -----------------------------------------------------------------------
# 用户关注的特殊 block 手牌
# -----------------------------------------------------------------------


class TestSpecificBlocks:
    """
    针对用户提出的几种容易出错的 block 手牌：
      22223333 / 23334 / 233334 / 33345 / 333345
    验证解析器能找到正确数量的拆分以及具体面子内容。
    """

    def test_22223333_with_234_bridge(self, parser):
        """
        22223333m456p11z (13) + win=4m →
        唯一拆法：[222m][333m][234m][456p] + 雀头1z
        （2m×4 + 3m×4 的 block 中，额外的 4m 只能和一个 2m/3m 组成顺子）
        """
        hand13 = parse_tiles_string("22223333m456p11z")
        win = Tile.from_string("4m")
        patterns = parser.parse(hand13, win)

        assert len(patterns) == 1
        p = patterns[0]
        assert p.jantou[0].to_string() == "1z"
        koutsu_tiles = sorted(t.to_string() for m in p.koutsu for t in m)
        assert koutsu_tiles == ["2m"] * 3 + ["3m"] * 3
        shuntsu_tiles_flat = sorted(t.to_string() for m in p.shuntsu for t in m)
        assert shuntsu_tiles_flat == ["2m", "3m", "4m", "4p", "5p", "6p"]

    def test_222333444_two_patterns(self, parser):
        """
        222333444m456p11z (14 张) →
        拆法1：[222m][333m][444m][456p] + 雀头1z （三暗刻）
        拆法2：[234m]×3 + [456p]  + 雀头1z （三色/一气通贯候选）
        这是 22223333 系列中最典型的双解情形。
        """
        hand14 = parse_tiles_string("222333444m456p11z")
        patterns = parser.parse(hand14)

        assert (
            len(patterns) == 2
        ), f"期望2种解析，实际{len(patterns)}种：\n" + "\n".join(
            str(sorted_mentsu_key(p)) for p in patterns
        )
        has_all_koutsu = any(
            len(p.koutsu) == 3 and len(p.shuntsu) == 1 for p in patterns
        )
        has_all_shuntsu = any(
            len(p.shuntsu) == 4 and len(p.koutsu) == 0 for p in patterns
        )
        assert has_all_koutsu, "应有全刻子拆法 [222m][333m][444m][456p]"
        assert has_all_shuntsu, "应有全顺子拆法 [234m]×3+[456p]"

    def test_23334_only_koutsu_shuntsu(self, parser):
        """
        23334m456p789s11z (13) + win=3m →
        唯一拆法：[333m][234m][456p][789s] + 雀头1z
        5 张 block 23334 不存在多解。
        """
        hand13 = parse_tiles_string("23334m456p789s11z")
        win = Tile.from_string("3m")
        patterns = parser.parse(hand13, win)

        assert len(patterns) == 1
        p = patterns[0]
        assert p.jantou[0].to_string() == "1z"
        assert len(p.koutsu) == 1
        assert p.koutsu[0][0].to_string() == "3m"
        shuntsu_starts = sorted(m[0].to_string() for m in p.shuntsu)
        assert shuntsu_starts == ["2m", "4p", "7s"]

    def test_23334_wrong_wait_no_pattern(self, parser):
        """
        23334m 等 2m（非正确等牌）→ 0 种解析
        """
        hand13 = parse_tiles_string("23334m456p789s11z")
        win = Tile.from_string("2m")
        patterns = parser.parse(hand13, win)
        assert len(patterns) == 0

    def test_233334_unique_pattern(self, parser):
        """
        233334m456p789s1z (13) + win=1z →
        唯一拆法：[333m][234m][456p][789s] + 雀头1z
        6 张 block 233334 无歧义。
        """
        hand13 = parse_tiles_string("233334m456p789s1z")
        win = Tile.from_string("1z")
        patterns = parser.parse(hand13, win)

        assert len(patterns) == 1
        p = patterns[0]
        assert p.jantou[0].to_string() == "1z"
        assert len(p.koutsu) == 1
        assert p.koutsu[0][0].to_string() == "3m"

    def test_33345_wait_6s(self, parser):
        """
        33345s123p789m11z (13) + win=6s →
        唯一拆法：[333s][456s][123p][789m] + 雀头1z
        """
        hand13 = parse_tiles_string("33345s123p789m11z")
        win = Tile.from_string("6s")
        patterns = parser.parse(hand13, win)

        assert len(patterns) == 1
        p = patterns[0]
        assert p.jantou[0].to_string() == "1z"
        assert len(p.koutsu) == 1
        assert p.koutsu[0][0].to_string() == "3s"
        shuntsu_starts = sorted(m[0].to_string() for m in p.shuntsu)
        assert shuntsu_starts == ["4s", "7m", "1p"].__class__(
            sorted(["4s", "1p", "7m"])
        )

    def test_33345_wait_3s(self, parser):
        """
        33345s123p789m11z (13) + win=3s →
        唯一拆法：[333s][345s][123p][789m] + 雀头1z
        同一个 block 不同等牌产生不同面子组成。
        """
        hand13 = parse_tiles_string("33345s123p789m11z")
        win = Tile.from_string("3s")
        patterns = parser.parse(hand13, win)

        assert len(patterns) == 1
        p = patterns[0]
        assert p.jantou[0].to_string() == "1z"
        assert len(p.koutsu) == 1
        assert p.koutsu[0][0].to_string() == "3s"
        shuntsu_starts = sorted(m[0].to_string() for m in p.shuntsu)
        assert shuntsu_starts == sorted(["3s", "1p", "7m"])

    def test_333345_direct_14(self, parser):
        """
        333345s123p789m11z (14 张, 直接输入) →
        唯一拆法：[333s][345s][123p][789m] + 雀头1z
        """
        hand14 = parse_tiles_string("333345s123p789m11z")
        patterns = parser.parse(hand14)

        assert len(patterns) == 1
        p = patterns[0]
        assert p.jantou[0].to_string() == "1z"
        assert len(p.koutsu) == 1
        assert p.koutsu[0][0].to_string() == "3s"

    def test_33345_tenpai_both_waits(self, parser):
        """
        33345s123p789m11z (13 张) 应同时听 3s 和 6s 两张牌
        """
        hand13 = parse_tiles_string("33345s123p789m11z")
        assert parser.is_tenpai(hand13) is True

        # 确认两张等牌都能和
        win_3s = parser.parse(hand13, Tile.from_string("3s"))
        win_6s = parser.parse(hand13, Tile.from_string("6s"))
        assert len(win_3s) >= 1, "等 3s 应能和牌"
        assert len(win_6s) >= 1, "等 6s 应能和牌"

        # 确认不相关的牌不能和
        win_2s = parser.parse(hand13, Tile.from_string("2s"))
        assert len(win_2s) == 0, "等 2s 不应能和牌"
