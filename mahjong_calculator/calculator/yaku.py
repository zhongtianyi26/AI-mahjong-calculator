"""
役种判断模块 - 判断手牌包含哪些役
"""

from typing import List, Tuple, Set, Optional
from collections import Counter
from .tiles import Tile, TileType, Meld
from .parser import HandParser, MentsuPattern


class Yaku:
    """役种定义"""

    # 1番役
    RIICHI = ("立直", 1)
    IPPATSU = ("一发", 1)
    TSUMO = ("门前清自摸", 1)
    TANYAO = ("断幺九", 1)
    YAKUHAI_TON = ("役牌:东", 1)
    YAKUHAI_NAN = ("役牌:南", 1)
    YAKUHAI_SHA = ("役牌:西", 1)
    YAKUHAI_PEI = ("役牌:北", 1)
    YAKUHAI_HAKU = ("役牌:白", 1)
    YAKUHAI_HATSU = ("役牌:发", 1)
    YAKUHAI_CHUN = ("役牌:中", 1)
    PINFU = ("平和", 1)
    IIPEIKOU = ("一杯口", 1)
    HAITEI = ("海底捞月", 1)
    HOUTEI = ("河底捞鱼", 1)
    RINSHAN = ("岭上开花", 1)
    CHANKAN = ("抢杠", 1)

    # 2番役
    DOUBLE_RIICHI = ("双立直", 2)
    TOITOI = ("对对和", 2)
    SANANKOU = ("三暗刻", 2)
    SANSHOKU_DOUJUN = ("三色同顺", 2)
    SANSHOKU_DOUKOU = ("三色同刻", 2)
    SANKANTSU = ("三杠子", 2)
    ITTSU = ("一气通贯", 2)
    CHANTA = ("混全带幺九", 2)
    CHIITOITSU = ("七对子", 2)
    HONROUTOU = ("混老头", 2)
    SHOUSANGEN = ("小三元", 2)

    # 3番役
    HONITSU = ("混一色", 3)
    JUNCHAN = ("纯全带幺九", 3)
    RYANPEIKOU = ("二杯口", 3)

    # 6番役
    CHINITSU = ("清一色", 6)

    # 役满
    KOKUSHI = ("国士无双", 13)
    SUUANKOU = ("四暗刻", 13)
    DAISANGEN = ("大三元", 13)
    SHOUSUUSHI = ("小四喜", 13)
    DAISUUSHI = ("大四喜", 26)
    TSUUIISOU = ("字一色", 13)
    RYUUIISOU = ("绿一色", 13)
    CHINROUTOU = ("清老头", 13)
    CHUUREN = ("九莲宝灯", 13)
    SUUKANTSU = ("四杠子", 13)
    TENHOU = ("天和", 13)
    CHIIHOU = ("地和", 13)


class YakuChecker:
    """
    役种检查器

    检查手牌包含哪些役种
    """

    def __init__(self):
        self.parser = HandParser()

    def check_yaku(
        self,
        hand: List[Tile],
        win_tile: Tile,
        patterns: List[MentsuPattern],
        is_tsumo: bool = False,
        is_riichi: bool = False,
        is_double_riichi: bool = False,
        is_ippatsu: bool = False,
        is_menzen: bool = True,
        is_haitei: bool = False,
        is_houtei: bool = False,
        is_rinshan: bool = False,
        is_chankan: bool = False,
        is_tenhou: bool = False,
        is_chiihou: bool = False,
        prevalent_wind: str = "E",
        seat_wind: str = "E",
        dora_tiles: List[Tile] = None,
        melds: List[Meld] = None,
    ) -> List[Tuple[str, int]]:
        """
        检查所有役种

        Args:
            hand: 手牌（13张，不含和牌）
            win_tile: 和牌
            patterns: 面子组合模式列表
            is_tsumo: 是否自摸
            is_riichi: 是否立直
            is_double_riichi: 是否双立直
            is_ippatsu: 是否一发
            is_menzen: 是否门前清（无副露）
            is_haitei: 是否海底捞月
            is_houtei: 是否河底捞鱼
            is_rinshan: 是否岭上开花
            is_chankan: 是否抢杠
            is_tenhou: 是否天和
            is_chiihou: 是否地和
            prevalent_wind: 场风（E/S/W/N）
            seat_wind: 自风（E/S/W/N）
            dora_tiles: 宝牌列表
            melds: 副露列表

        Returns:
            役种列表，每项为(役名, 番数)
        """
        if not patterns:
            return []

        all_tiles = hand + [win_tile]

        # 遍历所有面子拆分方式，选择番数最高的一种
        best_yaku_list: List[Tuple[str, int]] = []
        best_han = -1

        for pattern in patterns:
            yaku_list = self._check_yaku_for_pattern(
                all_tiles=all_tiles,
                pattern=pattern,
                win_tile=win_tile,
                is_tsumo=is_tsumo,
                is_riichi=is_riichi,
                is_double_riichi=is_double_riichi,
                is_ippatsu=is_ippatsu,
                is_menzen=is_menzen,
                is_haitei=is_haitei,
                is_houtei=is_houtei,
                is_rinshan=is_rinshan,
                is_chankan=is_chankan,
                is_tenhou=is_tenhou,
                is_chiihou=is_chiihou,
                prevalent_wind=prevalent_wind,
                seat_wind=seat_wind,
                melds=melds,
            )
            total_han = sum(h for _, h in yaku_list)
            if total_han > best_han:
                best_han = total_han
                best_yaku_list = yaku_list

        return best_yaku_list

    def _check_yaku_for_pattern(
        self,
        all_tiles: List[Tile],
        pattern: MentsuPattern,
        win_tile: Tile,
        is_tsumo: bool = False,
        is_riichi: bool = False,
        is_double_riichi: bool = False,
        is_ippatsu: bool = False,
        is_menzen: bool = True,
        is_haitei: bool = False,
        is_houtei: bool = False,
        is_rinshan: bool = False,
        is_chankan: bool = False,
        is_tenhou: bool = False,
        is_chiihou: bool = False,
        prevalent_wind: str = "E",
        seat_wind: str = "E",
        melds: List[Meld] = None,
    ) -> List[Tuple[str, int]]:
        """
        针对单个面子组合检查所有役种

        Returns:
            该拆法下的役种列表
        """
        yaku_list: List[Tuple[str, int]] = []

        # 检查役满
        yakuman = self._check_yakuman(
            all_tiles, pattern, is_menzen, is_tenhou, is_chiihou
        )
        if yakuman:
            return yakuman

        # 状态役
        if is_double_riichi:
            yaku_list.append(Yaku.DOUBLE_RIICHI)
        elif is_riichi:
            yaku_list.append(Yaku.RIICHI)

        if is_ippatsu and (is_riichi or is_double_riichi):
            yaku_list.append(Yaku.IPPATSU)

        if is_tsumo and is_menzen:
            yaku_list.append(Yaku.TSUMO)

        if is_haitei:
            yaku_list.append(Yaku.HAITEI)

        if is_houtei:
            yaku_list.append(Yaku.HOUTEI)

        if is_rinshan:
            yaku_list.append(Yaku.RINSHAN)

        if is_chankan:
            yaku_list.append(Yaku.CHANKAN)

        # 检查七对子
        if self.parser.is_chiitoitsu(all_tiles):
            yaku_list.append(Yaku.CHIITOITSU)
            # 七对子不能有其他面子役，直接返回
            return yaku_list

        # 检查其他役种
        if self._check_pinfu(
            pattern, win_tile, is_menzen, is_tsumo, seat_wind, prevalent_wind
        ):
            yaku_list.append(Yaku.PINFU)

        if self._check_tanyao(all_tiles):
            yaku_list.append(Yaku.TANYAO)

        # 役牌
        yakuhai = self._check_yakuhai(pattern, prevalent_wind, seat_wind)
        yaku_list.extend(yakuhai)

        # 一杯口和二杯口
        if is_menzen:
            if self._check_ryanpeikou(pattern):
                yaku_list.append(Yaku.RYANPEIKOU)
            elif self._check_iipeikou(pattern):
                yaku_list.append(Yaku.IIPEIKOU)

        # 三色同顺
        if self._check_sanshoku_doujun(pattern):
            yaku_list.append(Yaku.SANSHOKU_DOUJUN)

        # 一气通贯
        if self._check_ittsu(pattern):
            yaku_list.append(Yaku.ITTSU)

        # 对对和
        if self._check_toitoi(pattern):
            yaku_list.append(Yaku.TOITOI)

        # 三暗刻
        if self._check_sanankou(pattern, win_tile, is_tsumo, melds):
            yaku_list.append(Yaku.SANANKOU)

        # 三色同刻
        if self._check_sanshoku_doukou(pattern):
            yaku_list.append(Yaku.SANSHOKU_DOUKOU)

        # 混全带幺九
        if self._check_chanta(pattern):
            yaku_list.append(Yaku.CHANTA)

        # 纯全带幺九
        if self._check_junchan(pattern):
            yaku_list.append(Yaku.JUNCHAN)

        # 混老头
        if self._check_honroutou(all_tiles):
            yaku_list.append(Yaku.HONROUTOU)

        # 小三元
        if self._check_shousangen(pattern):
            yaku_list.append(Yaku.SHOUSANGEN)

        # 混一色
        if self._check_honitsu(all_tiles):
            han = 3 if is_menzen else 2
            yaku_list.append(("混一色", han))

        # 清一色
        if self._check_chinitsu(all_tiles):
            han = 6 if is_menzen else 5
            yaku_list.append(("清一色", han))

        return yaku_list

    def _check_yakuman(
        self,
        tiles: List[Tile],
        pattern: MentsuPattern,
        is_menzen: bool,
        is_tenhou: bool,
        is_chiihou: bool,
    ) -> Optional[List[Tuple[str, int]]]:
        """检查役满"""
        yakuman = []

        # 天和/地和
        if is_tenhou:
            return [Yaku.TENHOU]
        if is_chiihou:
            return [Yaku.CHIIHOU]

        # 国士无双
        if self.parser.is_kokushi(tiles):
            return [Yaku.KOKUSHI]

        # 四暗刻
        if self._check_suuankou(pattern, is_menzen):
            return [Yaku.SUUANKOU]

        # 大三元
        if self._check_daisangen(pattern):
            return [Yaku.DAISANGEN]

        # 字一色
        if self._check_tsuuiisou(tiles):
            return [Yaku.TSUUIISOU]

        # 清老头
        if self._check_chinroutou(tiles):
            return [Yaku.CHINROUTOU]

        # 大四喜
        if self._check_daisuushi(pattern):
            return [Yaku.DAISUUSHI]

        # 小四喜
        if self._check_shousuushi(pattern):
            return [Yaku.SHOUSUUSHI]

        return yakuman if yakuman else None

    def _check_pinfu(
        self,
        pattern: MentsuPattern,
        win_tile: Tile,
        is_menzen: bool,
        is_tsumo: bool,
        seat_wind: str,
        prevalent_wind: str,
    ) -> bool:
        """
        平和判断

        条件：
        1. 门前清
        2. 4个顺子 + 1个非役牌雀头
        3. 两面听牌
        """
        if not is_menzen:
            return False

        # 必须是4个顺子
        if len(pattern.shuntsu) != 4 or len(pattern.koutsu) != 0:
            return False

        # 雀头不能是役牌
        if pattern.jantou:
            jantou_tile = pattern.jantou[0]
            if self._is_yakuhai_tile(jantou_tile, seat_wind, prevalent_wind):
                return False

        # 检查是否两面听（这里简化处理）
        # 实际需要检查和牌是否在顺子的中间位置
        for shuntsu in pattern.shuntsu:
            if win_tile == shuntsu[1]:  # 和牌在顺子中间
                return True

        return False

    def _check_tanyao(self, tiles: List[Tile]) -> bool:
        """
        断幺九判断

        条件：全部是中张牌（2-8）
        """
        return all(tile.is_simple() for tile in tiles)

    def _check_yakuhai(
        self, pattern: MentsuPattern, prevalent_wind: str, seat_wind: str
    ) -> List[Tuple[str, int]]:
        """役牌判断"""
        yakuhai = []

        # 统计字牌刻子
        for koutsu in pattern.koutsu:
            tile = koutsu[0]
            if tile.is_honor():
                # 风牌
                if tile.value == 1 and (prevalent_wind == "E" or seat_wind == "E"):
                    yakuhai.append(Yaku.YAKUHAI_TON)
                elif tile.value == 2 and (prevalent_wind == "S" or seat_wind == "S"):
                    yakuhai.append(Yaku.YAKUHAI_NAN)
                elif tile.value == 3 and (prevalent_wind == "W" or seat_wind == "W"):
                    yakuhai.append(Yaku.YAKUHAI_SHA)
                elif tile.value == 4 and (prevalent_wind == "N" or seat_wind == "N"):
                    yakuhai.append(Yaku.YAKUHAI_PEI)
                # 三元牌
                elif tile.value == 5:
                    yakuhai.append(Yaku.YAKUHAI_HAKU)
                elif tile.value == 6:
                    yakuhai.append(Yaku.YAKUHAI_HATSU)
                elif tile.value == 7:
                    yakuhai.append(Yaku.YAKUHAI_CHUN)

        return yakuhai

    def _is_yakuhai_tile(self, tile: Tile, seat_wind: str, prevalent_wind: str) -> bool:
        """判断是否是役牌"""
        if not tile.is_honor():
            return False

        # 风牌
        wind_map = {"E": 1, "S": 2, "W": 3, "N": 4}
        if tile.value in [wind_map.get(seat_wind), wind_map.get(prevalent_wind)]:
            return True

        # 三元牌
        if tile.is_dragon():
            return True

        return False

    def _check_iipeikou(self, pattern: MentsuPattern) -> bool:
        """
        一杯口判断

        条件：有两组相同的顺子
        """
        if len(pattern.shuntsu) < 2:
            return False

        # 检查是否有重复的顺子
        shuntsu_set = set()
        for shuntsu in pattern.shuntsu:
            key = (shuntsu[0], shuntsu[1], shuntsu[2])
            if key in shuntsu_set:
                return True
            shuntsu_set.add(key)

        return False

    def _check_ryanpeikou(self, pattern: MentsuPattern) -> bool:
        """
        二杯口判断

        条件：有两对相同的顺子（4个顺子组成2对）
        """
        if len(pattern.shuntsu) != 4:
            return False

        # 统计每种顺子的数量
        shuntsu_counts = Counter()
        for shuntsu in pattern.shuntsu:
            key = (shuntsu[0], shuntsu[1], shuntsu[2])
            shuntsu_counts[key] += 1

        # 必须有两组各出现2次
        counts = list(shuntsu_counts.values())
        counts.sort()
        return counts == [2, 2]

    def _check_sanshoku_doujun(self, pattern: MentsuPattern) -> bool:
        """
        三色同顺判断

        条件：万筒索各有一组相同数字的顺子
        """
        if len(pattern.shuntsu) < 3:
            return False

        # 按花色分组顺子
        by_type = {TileType.MANZU: [], TileType.PINZU: [], TileType.SOUZU: []}
        for shuntsu in pattern.shuntsu:
            tile_type = shuntsu[0].tile_type
            if tile_type in by_type:
                values = (shuntsu[0].value, shuntsu[1].value, shuntsu[2].value)
                by_type[tile_type].append(values)

        # 检查是否有相同的顺子数字组合
        for m_values in by_type[TileType.MANZU]:
            if (
                m_values in by_type[TileType.PINZU]
                and m_values in by_type[TileType.SOUZU]
            ):
                return True

        return False

    def _check_ittsu(self, pattern: MentsuPattern) -> bool:
        """
        一气通贯判断

        条件：同一花色有123、456、789三组顺子
        """
        if len(pattern.shuntsu) < 3:
            return False

        # 按花色分组
        by_type = {TileType.MANZU: set(), TileType.PINZU: set(), TileType.SOUZU: set()}
        for shuntsu in pattern.shuntsu:
            tile_type = shuntsu[0].tile_type
            if tile_type in by_type:
                start_value = shuntsu[0].value
                by_type[tile_type].add(start_value)

        # 检查是否有1、4、7开头的顺子
        for values in by_type.values():
            if 1 in values and 4 in values and 7 in values:
                return True

        return False

    def _check_toitoi(self, pattern: MentsuPattern) -> bool:
        """对对和判断：4个刻子"""
        return len(pattern.koutsu) == 4

    def _check_sanankou(
        self, pattern: MentsuPattern, win_tile: Tile, is_tsumo: bool, melds: List[Meld]
    ) -> bool:
        """
        三暗刻判断

        条件：有3个暗刻（未副露的刻子）
        """
        if len(pattern.koutsu) < 3:
            return False

        # 计算暗刻数量
        ankou_count = 0
        for koutsu in pattern.koutsu:
            # 如果是自摸，或者和牌不在这个刻子中，则为暗刻
            if is_tsumo or win_tile not in koutsu:
                ankou_count += 1

        return ankou_count >= 3

    def _check_sanshoku_doukou(self, pattern: MentsuPattern) -> bool:
        """
        三色同刻判断

        条件：万筒索各有一组相同数字的刻子
        """
        if len(pattern.koutsu) < 3:
            return False

        # 按花色分组刻子
        by_type = {TileType.MANZU: set(), TileType.PINZU: set(), TileType.SOUZU: set()}
        for koutsu in pattern.koutsu:
            tile_type = koutsu[0].tile_type
            if tile_type in by_type:
                by_type[tile_type].add(koutsu[0].value)

        # 检查是否有相同数字
        for value in by_type[TileType.MANZU]:
            if value in by_type[TileType.PINZU] and value in by_type[TileType.SOUZU]:
                return True

        return False

    def _check_chanta(self, pattern: MentsuPattern) -> bool:
        """
        混全带幺九判断

        条件：每组面子和雀头都包含幺九牌
        """
        # 检查每个顺子
        for shuntsu in pattern.shuntsu:
            if not (shuntsu[0].is_terminal() or shuntsu[2].is_terminal()):
                return False

        # 检查每个刻子
        for koutsu in pattern.koutsu:
            if not koutsu[0].is_terminal():
                return False

        # 检查雀头
        if pattern.jantou and not pattern.jantou[0].is_terminal():
            return False

        return True

    def _check_junchan(self, pattern: MentsuPattern) -> bool:
        """
        纯全带幺九判断

        条件：每组面子和雀头都包含老头牌（19），不能有字牌
        """
        all_tiles = []
        for shuntsu in pattern.shuntsu:
            all_tiles.extend(shuntsu)
        for koutsu in pattern.koutsu:
            all_tiles.extend(koutsu)
        if pattern.jantou:
            all_tiles.extend(pattern.jantou)

        # 不能有字牌
        if any(tile.is_honor() for tile in all_tiles):
            return False

        # 检查每个面子都包含19
        for shuntsu in pattern.shuntsu:
            if not (shuntsu[0].value == 1 or shuntsu[2].value == 9):
                return False

        for koutsu in pattern.koutsu:
            if koutsu[0].value not in [1, 9]:
                return False

        if pattern.jantou and pattern.jantou[0].value not in [1, 9]:
            return False

        return True

    def _check_honroutou(self, tiles: List[Tile]) -> bool:
        """混老头判断：全部是幺九牌"""
        return all(tile.is_terminal() for tile in tiles)

    def _check_shousangen(self, pattern: MentsuPattern) -> bool:
        """
        小三元判断

        条件：白发中中有2个刻子，1个雀头
        """
        dragon_koutsu = 0
        dragon_jantou = False

        for koutsu in pattern.koutsu:
            if koutsu[0].is_dragon():
                dragon_koutsu += 1

        if pattern.jantou and pattern.jantou[0].is_dragon():
            dragon_jantou = True

        return dragon_koutsu == 2 and dragon_jantou

    def _check_honitsu(self, tiles: List[Tile]) -> bool:
        """
        混一色判断

        条件：只有一种花色的数牌+字牌
        """
        tile_types = set()
        has_jihai = False

        for tile in tiles:
            if tile.tile_type == TileType.JIHAI:
                has_jihai = True
            else:
                tile_types.add(tile.tile_type)

        # 必须有字牌，且只有一种数牌
        return has_jihai and len(tile_types) == 1

    def _check_chinitsu(self, tiles: List[Tile]) -> bool:
        """
        清一色判断

        条件：只有一种花色的数牌
        """
        tile_types = set()

        for tile in tiles:
            if tile.tile_type == TileType.JIHAI:
                return False
            tile_types.add(tile.tile_type)

        return len(tile_types) == 1

    def _check_suuankou(self, pattern: MentsuPattern, is_menzen: bool) -> bool:
        """四暗刻判断：4个暗刻"""
        return is_menzen and len(pattern.koutsu) == 4 and len(pattern.shuntsu) == 0

    def _check_daisangen(self, pattern: MentsuPattern) -> bool:
        """大三元判断：白发中都是刻子"""
        dragon_koutsu = 0
        for koutsu in pattern.koutsu:
            if koutsu[0].is_dragon():
                dragon_koutsu += 1
        return dragon_koutsu == 3

    def _check_tsuuiisou(self, tiles: List[Tile]) -> bool:
        """字一色判断：全部是字牌"""
        return all(tile.is_honor() for tile in tiles)

    def _check_chinroutou(self, tiles: List[Tile]) -> bool:
        """清老头判断：全部是19数牌"""
        for tile in tiles:
            if tile.is_honor():
                return False
            if tile.value not in [1, 9]:
                return False
        return True

    def _check_daisuushi(self, pattern: MentsuPattern) -> bool:
        """大四喜判断：东南西北都是刻子"""
        wind_koutsu = 0
        for koutsu in pattern.koutsu:
            if koutsu[0].is_wind():
                wind_koutsu += 1
        return wind_koutsu == 4

    def _check_shousuushi(self, pattern: MentsuPattern) -> bool:
        """小四喜判断：东南西北中3个刻子+1个雀头"""
        wind_koutsu = 0
        wind_jantou = False

        for koutsu in pattern.koutsu:
            if koutsu[0].is_wind():
                wind_koutsu += 1

        if pattern.jantou and pattern.jantou[0].is_wind():
            wind_jantou = True

        return wind_koutsu == 3 and wind_jantou
