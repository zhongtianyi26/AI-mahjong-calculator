"""
麻将计点计算器主类
"""

from typing import List, Optional, Dict, Tuple
from .tiles import Tile, parse_tiles_string, Meld
from .parser import HandParser
from .yaku import YakuChecker, Yaku
from .fu import FuCalculator
from .points import PointsCalculator
from .rules import GameRules, DEFAULT_RULES


class CalculationResult:
    """计算结果"""

    def __init__(self):
        self.yaku_list: List[Tuple[str, int]] = []  # 役种列表
        self.han: int = 0  # 总番数
        self.fu: Optional[int] = None  # 符数
        self.base_points: int = 0  # 基础点
        self.total_points: int = 0  # 总点数（含本场）
        self.payment_detail: str = ""  # 支付详情
        self.name: Optional[str] = None  # 特殊名称（满贯、役满等）
        self.dora_count: int = 0  # 宝牌总数（含表、里、赤）
        self.indicator_dora_count: int = 0  # 表宝牌数
        self.ura_dora_count: int = 0  # 里宝牌数
        self.red_dora_count: int = 0  # 赤宝牌数
        self.is_valid: bool = True  # 是否合法
        self.error_message: str = ""  # 错误信息

    def __repr__(self):
        if not self.is_valid:
            return f"CalculationResult(valid=False, error={self.error_message})"

        yaku_str = ", ".join([f"{name}({han}番)" for name, han in self.yaku_list])
        if self.name:
            return f"CalculationResult({self.name}: {yaku_str}, {self.han}番{self.fu}符 = {self.total_points}点)"
        else:
            return f"CalculationResult({yaku_str}, {self.han}番{self.fu}符 = {self.total_points}点)"


class Calculator:
    """
    麻将计点计算器

    提供简单易用的API接口
    """

    def __init__(self, rules: GameRules = None):
        """
        初始化计算器

        Args:
            rules: 游戏规则配置，默认使用日本麻将标准规则
        """
        self.rules = rules or DEFAULT_RULES
        self.parser = HandParser()
        self.yaku_checker = YakuChecker()
        self.fu_calculator = FuCalculator()
        self.points_calculator = PointsCalculator()

    def calculate(
        self,
        hand: str,
        win_tile: str,
        is_tsumo: bool = False,
        is_riichi: bool = False,
        is_double_riichi: bool = False,
        is_ippatsu: bool = False,
        is_dealer: bool = False,
        prevalent_wind: str = "E",
        seat_wind: str = "E",
        dora_indicators: List[str] = None,
        ura_dora_indicators: List[str] = None,
        is_haitei: bool = False,
        is_houtei: bool = False,
        is_rinshan: bool = False,
        is_chankan: bool = False,
        is_tenhou: bool = False,
        is_chiihou: bool = False,
        melds: List[Dict] = None,
        honba: int = 0,
    ) -> CalculationResult:
        """
        计算麻将点数

        Args:
            hand: 手牌字符串，如 "123m456p789s1122z"（13张，不含和牌）
            win_tile: 和牌，如 "2z"
            is_tsumo: 是否自摸
            is_riichi: 是否立直
            is_double_riichi: 是否双立直
            is_ippatsu: 是否一发
            is_dealer: 是否庄家
            prevalent_wind: 场风（E/S/W/N）
            seat_wind: 自风（E/S/W/N）
            dora_indicators: 宝牌指示牌列表
            ura_dora_indicators: 里宝指示牌列表
            is_haitei: 是否海底捞月
            is_houtei: 是否河底捞鱼
            is_rinshan: 是否岭上开花
            is_chankan: 是否抢杠
            is_tenhou: 是否天和
            is_chiihou: 是否地和
            melds: 副露列表
            honba: 本场数

        Returns:
            CalculationResult对象
        """
        result = CalculationResult()

        try:
            # 解析手牌
            hand_tiles = parse_tiles_string(hand)
            win_tile_obj = Tile.from_string(win_tile)

            # 检查手牌数量
            if len(hand_tiles) != 13:
                result.is_valid = False
                result.error_message = f"手牌必须是13张，当前为{len(hand_tiles)}张"
                return result

            # 判断是否门前清
            is_menzen = not melds or len(melds) == 0

            # 解析面子组合
            patterns = self.parser.parse(hand_tiles, win_tile_obj)

            if not patterns:
                result.is_valid = False
                result.error_message = "无法识别有效的和牌型"
                return result

            # ---- 计算宝牌番数（与拆法无关，提前算好）----
            dora_count = 0
            indicator_dora_count = 0
            ura_dora_count = 0

            all_tiles = hand_tiles + [win_tile_obj]

            if dora_indicators:
                dora_tiles = [self._get_dora_tile(ind) for ind in dora_indicators]
                for dora in dora_tiles:
                    cnt = sum(1 for tile in all_tiles if tile == dora)
                    indicator_dora_count += cnt
                    dora_count += cnt

            if ura_dora_indicators and (is_riichi or is_double_riichi):
                ura_dora_tiles = [
                    self._get_dora_tile(ind) for ind in ura_dora_indicators
                ]
                for dora in ura_dora_tiles:
                    cnt = sum(1 for tile in all_tiles if tile == dora)
                    ura_dora_count += cnt
                    dora_count += cnt

            # ---- 计算赤宝牌，合并进 dora_count ----
            red_dora_count = sum(1 for tile in all_tiles if tile.is_red)
            dora_count += red_dora_count

            result.dora_count = dora_count
            result.indicator_dora_count = indicator_dora_count
            result.ura_dora_count = ura_dora_count
            result.red_dora_count = red_dora_count

            # ---- 遍历所有拆法，逐个计算 (役→符→点数)，取最高分 ----
            best_total_points = -1
            best_yaku_list = None
            best_fu = None
            best_points_info = None

            for pattern in patterns:
                # 对该拆法检查役种
                cur_yaku = self.yaku_checker._check_yaku_for_pattern(
                    all_tiles=hand_tiles + [win_tile_obj],
                    pattern=pattern,
                    win_tile=win_tile_obj,
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
                    melds=None,
                )

                # 追加宝牌（已含赤宝牌）
                cur_yaku_with_dora = cur_yaku.copy()
                if dora_count > 0:
                    cur_yaku_with_dora.append((f"宝牌x{dora_count}", dora_count))

                cur_total_han = sum(h for _, h in cur_yaku_with_dora)

                # 跳过无役的拆法（宝牌不算役）
                if cur_total_han == 0 or (
                    dora_count > 0 and cur_total_han == dora_count
                ):
                    continue

                # 判断七对子/平和
                cur_is_chiitoitsu = any(
                    name == "七对子" for name, _ in cur_yaku_with_dora
                )
                cur_is_pinfu = any(name == "平和" for name, _ in cur_yaku_with_dora)

                # 计算符数
                cur_fu = self.fu_calculator.calculate(
                    pattern=pattern,
                    win_tile=win_tile_obj,
                    is_tsumo=is_tsumo,
                    is_menzen=is_menzen,
                    is_pinfu=cur_is_pinfu,
                    is_chiitoitsu=cur_is_chiitoitsu,
                    seat_wind=seat_wind,
                    prevalent_wind=prevalent_wind,
                )

                # 计算点数
                cur_points_info = self.points_calculator.calculate(
                    han=cur_total_han,
                    fu=cur_fu,
                    is_dealer=is_dealer,
                    is_tsumo=is_tsumo,
                    honba=honba,
                )

                cur_total_points = cur_points_info["total_points"]
                if cur_total_points > best_total_points:
                    best_total_points = cur_total_points
                    best_yaku_list = cur_yaku_with_dora
                    best_fu = cur_fu
                    best_points_info = cur_points_info

            # 所有拆法都无役
            if best_yaku_list is None:
                result.is_valid = False
                result.error_message = "无役（至少需要1个役种，宝牌不算役）"
                return result

            yaku_list = best_yaku_list
            total_han = sum(h for _, h in yaku_list)
            fu = best_fu
            points_info = best_points_info

            result.yaku_list = yaku_list
            result.han = total_han
            result.fu = fu

            result.total_points = points_info["total_points"]
            result.payment_detail = points_info["payment_detail"]
            result.name = points_info.get("name")

            return result

        except Exception as e:
            result.is_valid = False
            result.error_message = f"计算错误: {str(e)}"
            return result

    def _get_dora_tile(self, indicator: str) -> Tile:
        """
        根据宝牌指示牌获取实际宝牌

        Args:
            indicator: 宝牌指示牌字符串

        Returns:
            实际宝牌的Tile对象
        """
        ind_tile = Tile.from_string(indicator)

        # 字牌的宝牌规则
        if ind_tile.is_honor():
            # 东南西北 循环
            if ind_tile.is_wind():
                next_value = (ind_tile.value % 4) + 1
                return Tile(next_value, ind_tile.tile_type)
            # 白发中 循环
            else:
                if ind_tile.value == 7:
                    return Tile(5, ind_tile.tile_type)  # 中 -> 白
                else:
                    return Tile(ind_tile.value + 1, ind_tile.tile_type)

        # 数牌：9 -> 1
        if ind_tile.value == 9:
            return Tile(1, ind_tile.tile_type)
        else:
            return Tile(ind_tile.value + 1, ind_tile.tile_type)

    def check_tenpai(self, hand: str) -> bool:
        """
        检查是否听牌

        Args:
            hand: 手牌字符串（13张）

        Returns:
            是否听牌
        """
        try:
            hand_tiles = parse_tiles_string(hand)
            return self.parser.is_tenpai(hand_tiles)
        except:
            return False
