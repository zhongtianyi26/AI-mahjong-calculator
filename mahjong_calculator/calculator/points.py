"""
点数计算模块
"""

from typing import Dict, Tuple


class PointsCalculator:
    """
    点数计算器

    根据番数和符数计算最终点数
    """

    # 点数表（番数 -> 符数 -> 基础点）
    POINTS_TABLE = {
        1: {
            30: (1000, 500, 300),
            40: (1300, 700, 400),
            50: (1600, 800, 400),
            60: (2000, 1000, 500),
            70: (2300, 1200, 600),
            80: (2600, 1300, 700),
            90: (2900, 1500, 800),
            100: (3200, 1600, 800),
            110: (3600, 1800, 900),
        },
        2: {
            20: (1300, 700, 400),  # 平和自摸
            25: (1600, 800, 400),  # 七对子
            30: (2000, 1000, 500),
            40: (2600, 1300, 700),
            50: (3200, 1600, 800),
            60: (3900, 2000, 1000),
            70: (4500, 2300, 1200),
            80: (5200, 2600, 1300),
            90: (5800, 2900, 1500),
            100: (6400, 3200, 1600),
            110: (7100, 3600, 1800),
        },
        3: {
            20: (2600, 1300, 700),
            25: (3200, 1600, 800),
            30: (3900, 2000, 1000),
            40: (5200, 2600, 1300),
            50: (6400, 3200, 1600),
            60: (7700, 3900, 2000),
            70: (8000, 4000, 2000),  # 满贯
        },
        4: {
            20: (5200, 2600, 1300),
            25: (6400, 3200, 1600),
            30: (7700, 3900, 2000),
            # 4番30符以上都是满贯
        },
        # 5番以上都是满贯、跳满、倍满等
    }

    def calculate(
        self,
        han: int,
        fu: int,
        is_dealer: bool = False,
        is_tsumo: bool = False,
        honba: int = 0,
    ) -> Dict:
        """
        计算点数

        Args:
            han: 番数
            fu: 符数
            is_dealer: 是否庄家
            is_tsumo: 是否自摸
            honba: 本场数

        Returns:
            点数信息字典，包含：
            - base_points: 基础点
            - total_points: 总点数
            - dealer_pays: 庄家支付（自摸时）
            - non_dealer_pays: 闲家支付（自摸时）
            - direct_pay: 直接支付（荣和时）
        """
        # 处理役满
        if han >= 13:
            return self._calculate_yakuman(han, is_dealer, is_tsumo, honba)

        # 处理满贯、跳满、倍满、三倍满
        if han >= 5 or (han == 4 and fu >= 40) or (han == 3 and fu >= 70):
            return self._calculate_special(han, is_dealer, is_tsumo, honba)

        # 普通计算
        return self._calculate_normal(han, fu, is_dealer, is_tsumo, honba)

    def _calculate_normal(
        self, han: int, fu: int, is_dealer: bool, is_tsumo: bool, honba: int
    ) -> Dict:
        """计算普通点数（1-4番）"""
        result = {
            "han": han,
            "fu": fu,
            "is_dealer": is_dealer,
            "is_tsumo": is_tsumo,
            "honba": honba,
        }

        # 始终由公式推算基础点，确保各家付出额与总点数完全吻合
        # 基础点 = fu * 2^(han+2)，再按角色/方式乘以倍率后上舍入到100
        base = fu * (2 ** (han + 2))

        if is_tsumo:
            if is_dealer:
                # 庄家自摸：三家各付 base*2，上舍入到100
                each_pays = self._round_up(base * 2, 100)
                total = each_pays * 3
                result["total_points"] = total + honba * 300
                result["each_pays"] = each_pays + honba * 100
                result["payment_detail"] = f"各家支付 {each_pays + honba * 100} 点"
            else:
                # 闲家自摸：庄付 base*2，各闲付 base*1，均上舍入到100
                dealer_pays = self._round_up(base * 2, 100)
                non_dealer_pays = self._round_up(base, 100)
                total = dealer_pays + non_dealer_pays * 2
                result["total_points"] = total + honba * 300
                result["dealer_pays"] = dealer_pays + honba * 100
                result["non_dealer_pays"] = non_dealer_pays + honba * 100
                result["payment_detail"] = (
                    f"庄家支付 {dealer_pays + honba * 100} 点，"
                    f"闲家各支付 {non_dealer_pays + honba * 100} 点"
                )
        else:
            # 荣和：庄家 base*6，闲家 base*4，上舍入到100
            multiplier = 6 if is_dealer else 4
            direct = self._round_up(base * multiplier, 100)
            result["total_points"] = direct + honba * 300
            result["direct_pay"] = direct + honba * 300
            result["payment_detail"] = f"放铳者支付 {direct + honba * 300} 点"

        return result

    def _calculate_special(
        self, han: int, is_dealer: bool, is_tsumo: bool, honba: int
    ) -> Dict:
        """计算满贯、跳满、倍满、三倍满"""
        result = {
            "han": han,
            "fu": None,
            "is_dealer": is_dealer,
            "is_tsumo": is_tsumo,
            "honba": honba,
        }

        # 满贯（5番）：8000点（庄家12000）
        # 跳满（6-7番）：12000点（庄家18000）
        # 倍满（8-10番）：16000点（庄家24000）
        # 三倍满（11-12番）：24000点（庄家36000）

        if han <= 5:
            result["name"] = "满贯"
            base = 8000 if not is_dealer else 12000
        elif han <= 7:
            result["name"] = "跳满"
            base = 12000 if not is_dealer else 18000
        elif han <= 10:
            result["name"] = "倍满"
            base = 16000 if not is_dealer else 24000
        else:
            result["name"] = "三倍满"
            base = 24000 if not is_dealer else 36000

        if is_tsumo:
            if is_dealer:
                # 庄家自摸
                each_pays = base // 3
                result["total_points"] = base + honba * 300
                result["each_pays"] = each_pays + honba * 100
                result["payment_detail"] = f"各家支付 {each_pays + honba * 100} 点"
            else:
                # 闲家自摸
                dealer_pays = base // 2
                non_dealer_pays = base // 4
                result["total_points"] = base + honba * 300
                result["dealer_pays"] = dealer_pays + honba * 100
                result["non_dealer_pays"] = non_dealer_pays + honba * 100
                result["payment_detail"] = (
                    f"庄家支付 {dealer_pays + honba * 100} 点，闲家各支付 {non_dealer_pays + honba * 100} 点"
                )
        else:
            # 荣和
            result["total_points"] = base + honba * 300
            result["direct_pay"] = base + honba * 300
            result["payment_detail"] = f"放铳者支付 {base + honba * 300} 点"

        return result

    def _calculate_yakuman(
        self, han: int, is_dealer: bool, is_tsumo: bool, honba: int
    ) -> Dict:
        """计算役满"""
        result = {
            "han": han,
            "fu": None,
            "is_dealer": is_dealer,
            "is_tsumo": is_tsumo,
            "honba": honba,
        }

        # 役满：32000点（庄家48000）
        # 双倍役满：64000点（庄家96000）
        # 三倍役满：96000点（庄家144000）

        yakuman_count = han // 13
        result["yakuman_count"] = yakuman_count

        if yakuman_count == 1:
            result["name"] = "役满"
            base = 32000 if not is_dealer else 48000
        elif yakuman_count == 2:
            result["name"] = "双倍役满"
            base = 64000 if not is_dealer else 96000
        else:
            result["name"] = f"{yakuman_count}倍役满"
            base = 32000 * yakuman_count if not is_dealer else 48000 * yakuman_count

        if is_tsumo:
            if is_dealer:
                # 庄家自摸
                each_pays = base // 3
                result["total_points"] = base + honba * 300
                result["each_pays"] = each_pays + honba * 100
                result["payment_detail"] = f"各家支付 {each_pays + honba * 100} 点"
            else:
                # 闲家自摸
                dealer_pays = base // 2
                non_dealer_pays = base // 4
                result["total_points"] = base + honba * 300
                result["dealer_pays"] = dealer_pays + honba * 100
                result["non_dealer_pays"] = non_dealer_pays + honba * 100
                result["payment_detail"] = (
                    f"庄家支付 {dealer_pays + honba * 100} 点，闲家各支付 {non_dealer_pays + honba * 100} 点"
                )
        else:
            # 荣和
            result["total_points"] = base + honba * 300
            result["direct_pay"] = base + honba * 300
            result["payment_detail"] = f"放铳者支付 {base + honba * 300} 点"

        return result

    def _round_up(self, value: int, unit: int) -> int:
        """向上取整到指定单位"""
        return ((value + unit - 1) // unit) * unit
