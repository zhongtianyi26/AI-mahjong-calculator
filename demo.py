"""
临时可视化演示脚本 —— 随机生成可和手牌并交互式计算点数
后续可直接删除此文件，不影响核心代码。
"""

import random
import sys
from collections import Counter
from typing import List, Optional, Tuple

from mahjong_calculator.calculator.tiles import (
    Tile,
    TileType,
    parse_tiles_string,
    tiles_to_string,
)
from mahjong_calculator.calculator.parser import HandParser
from mahjong_calculator.calculator.calculator import Calculator

# ─── 常量 ──────────────────────────────────────────────
WIND_NAMES = {"E": "东", "S": "南", "W": "西", "N": "北"}
WIND_LIST = ["E", "S", "W", "N"]
TILE_DISPLAY = {
    "1m": "一万",
    "2m": "二万",
    "3m": "三万",
    "4m": "四万",
    "5m": "五万",
    "6m": "六万",
    "7m": "七万",
    "8m": "八万",
    "9m": "九万",
    "1p": "一筒",
    "2p": "二筒",
    "3p": "三筒",
    "4p": "四筒",
    "5p": "五筒",
    "6p": "六筒",
    "7p": "七筒",
    "8p": "八筒",
    "9p": "九筒",
    "1s": "一索",
    "2s": "二索",
    "3s": "三索",
    "4s": "四索",
    "5s": "五索",
    "6s": "六索",
    "7s": "七索",
    "8s": "八索",
    "9s": "九索",
    "1z": "东",
    "2z": "南",
    "3z": "西",
    "4z": "北",
    "5z": "白",
    "6z": "发",
    "7z": "中",
    "0m": "赤五万",
    "0p": "赤五筒",
    "0s": "赤五索",
}


# ─── 牌山 ──────────────────────────────────────────────
def build_wall(use_red_dora: bool = True) -> List[Tile]:
    """
    构建一副完整的牌山 (136张)。
    每种牌各 4 张；如果启用赤宝牌，则 5m/5p/5s 各有一张替换为赤五。
    """
    wall: List[Tile] = []
    for suit in [TileType.MANZU, TileType.PINZU, TileType.SOUZU]:
        for v in range(1, 10):
            for copy_idx in range(4):
                if use_red_dora and v == 5 and copy_idx == 0:
                    wall.append(Tile(5, suit, is_red=True))
                else:
                    wall.append(Tile(v, suit))
    for v in range(1, 8):
        for _ in range(4):
            wall.append(Tile(v, TileType.JIHAI))
    random.shuffle(wall)
    return wall


# ─── 随机生成可和手牌 ─────────────────────────────────
def generate_winning_hand(
    wall: List[Tile],
) -> Optional[Tuple[List[Tile], Tile, List[Tile]]]:
    """
    从牌山中随机抽取手牌，使其恰好可以和牌。
    返回 (hand_13, win_tile, remaining_wall)
    如果多次尝试都无法生成，返回 None。
    """
    parser = HandParser()
    for _ in range(2000):
        random.shuffle(wall)
        # 随机选 14 张
        sample14 = wall[:14]
        rest = wall[14:]
        if parser.parse(sample14[:13], sample14[13]):
            return sample14[:13], sample14[13], rest
    return None


def display_tile(tile: Tile) -> str:
    """可视化单张牌"""
    key = tile.to_string()
    return TILE_DISPLAY.get(key, key)


def display_tiles(tiles: List[Tile]) -> str:
    """可视化牌列表"""
    return " ".join(display_tile(t) for t in sorted(tiles))


def display_tiles_compact(tiles: List[Tile]) -> str:
    """紧凑编码 + 中文"""
    compact = tiles_to_string(sorted(tiles))
    chinese = display_tiles(tiles)
    return f"{compact}  ({chinese})"


# ─── 随机场况 ─────────────────────────────────────────
def random_game_context() -> dict:
    prevalent = random.choice(WIND_LIST)
    seat = random.choice(WIND_LIST)
    is_dealer = seat == prevalent  # 简化：场风==自风即为庄
    honba = random.randint(0, 3)
    return {
        "prevalent_wind": prevalent,
        "seat_wind": seat,
        "is_dealer": is_dealer,
        "honba": honba,
    }


# ─── 从剩余牌山中抽宝牌指示牌 ──────────────────────────
def draw_dora_indicators(
    remaining_wall: List[Tile], kan_count: int = 0
) -> Tuple[List[str], List[str]]:
    """
    抽取宝牌指示牌和里宝牌指示牌。
    基础 1 张表宝牌 + 每开一杠多 1 张，里宝牌同理。
    """
    total = 1 + kan_count  # 表宝牌张数
    random.shuffle(remaining_wall)

    dora_ind = [t.to_string() for t in remaining_wall[:total]]
    ura_ind = [t.to_string() for t in remaining_wall[total : total * 2]]
    return dora_ind, ura_ind


# ─── 交互选择 ─────────────────────────────────────────
def yes_no(prompt: str, default: bool = False) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    ans = input(f"  {prompt} {hint}: ").strip().lower()
    if ans == "":
        return default
    return ans in ("y", "yes", "是")


def choose_one(prompt: str, options: List[str], default_idx: int = 0) -> int:
    print(f"  {prompt}")
    for i, opt in enumerate(options):
        marker = " *" if i == default_idx else ""
        print(f"    [{i}] {opt}{marker}")
    ans = input(f"  请选择 (默认 {default_idx}): ").strip()
    if ans == "":
        return default_idx
    try:
        idx = int(ans)
        if 0 <= idx < len(options):
            return idx
    except ValueError:
        pass
    return default_idx


# ─── 主流程 ───────────────────────────────────────────
def main():
    print("=" * 60)
    print("  麻将计点可视化演示  (临时脚本，可直接删除)")
    print("=" * 60)

    calc = Calculator()
    parser = HandParser()

    while True:
        print("\n─── 生成新局面 ───")
        wall = build_wall(use_red_dora=True)
        result = generate_winning_hand(wall)
        if result is None:
            print("  ❌ 无法生成可和手牌，重试...")
            continue

        hand_tiles, win_tile, remaining = result
        ctx = random_game_context()

        # 杠数（随机 0~1，影响宝牌数量）
        kan_count = random.choice([0, 0, 0, 1])

        # 抽宝牌指示牌
        dora_indicators, ura_dora_indicators = draw_dora_indicators(
            remaining, kan_count
        )

        # ─── 展示场况 ────────────────────────────────
        print(f"\n  场风: {WIND_NAMES[ctx['prevalent_wind']]}风场")
        print(f"  自风: {WIND_NAMES[ctx['seat_wind']]}")
        print(f"  身份: {'亲家 (庄家)' if ctx['is_dealer'] else '子家 (闲家)'}")
        print(f"  本场: {ctx['honba']} 本场")
        if kan_count > 0:
            print(f"  开杠: {kan_count} 杠 (额外宝牌指示牌)")
        print()

        # ─── 展示手牌 ────────────────────────────────
        print(f"  手牌 (13张): {display_tiles_compact(hand_tiles)}")
        print(f"  和牌:        {display_tile(win_tile)} ({win_tile.to_string()})")
        print()

        # ─── 宝牌指示牌 ──────────────────────────────
        print(f"  宝牌指示牌 ({len(dora_indicators)}张):")
        for ind in dora_indicators:
            dora = calc._get_dora_tile(ind)
            print(
                f"    指示牌 {display_tile(Tile.from_string(ind))} → 宝牌 {display_tile(dora)}"
            )
        print()

        # ─── 手动选项 ────────────────────────────────
        print("  ── 和牌条件 ──")
        win_method = choose_one("和牌方式:", ["自摸 (ツモ)", "荣和 (ロン)"])
        is_tsumo = win_method == 0

        is_riichi = yes_no("立直?")
        is_double_riichi = False
        is_ippatsu = False
        if is_riichi:
            is_double_riichi = yes_no("双立直?")
            is_ippatsu = yes_no("一发?")

        is_haitei = False
        is_houtei = False
        is_rinshan = False
        is_chankan = False

        if is_tsumo:
            is_haitei = yes_no("海底捞月 (最后一张自摸)?")
            if kan_count > 0:
                is_rinshan = yes_no("岭上开花 (杠后摸牌)?")
        else:
            is_houtei = yes_no("河底捞鱼 (最后一张荣和)?")
            is_chankan = yes_no("抢杠?")

        # ─── 里宝牌 ──────────────────────────────────
        show_ura = is_riichi or is_double_riichi
        if show_ura:
            print(f"\n  里宝牌指示牌 ({len(ura_dora_indicators)}张):")
            for ind in ura_dora_indicators:
                dora = calc._get_dora_tile(ind)
                print(
                    f"    指示牌 {display_tile(Tile.from_string(ind))} → 里宝牌 {display_tile(dora)}"
                )
        else:
            ura_dora_indicators = None
            print("\n  (非立直，无里宝牌)")

        # ─── 解析拆法 ────────────────────────────────
        print("\n  ── 手牌拆解 ──")
        patterns = parser.parse(hand_tiles, win_tile)
        if not patterns:
            print("  ❌ 无法拆解为合法和牌型")
            _continue_or_quit()
            continue

        for i, pat in enumerate(patterns):
            print(f"  拆法 {i + 1}:")
            if pat.jantou:
                head = pat.jantou
                print(f"    雀头: {display_tile(head[0])} {display_tile(head[1])}")
            if pat.shuntsu:
                for s in pat.shuntsu:
                    print(
                        f"    顺子: {display_tile(s[0])} {display_tile(s[1])} {display_tile(s[2])}"
                    )
            if pat.koutsu:
                for k in pat.koutsu:
                    print(
                        f"    刻子: {display_tile(k[0])} {display_tile(k[1])} {display_tile(k[2])}"
                    )
            if not pat.jantou and not pat.shuntsu and not pat.koutsu:
                # 特殊型（七对子/国士）
                all14 = sorted(hand_tiles + [win_tile])
                from collections import Counter as C

                cnt = C(all14)
                if len(cnt) == 7 and all(v == 2 for v in cnt.values()):
                    print(f"    七对子: {display_tiles(all14)}")
                else:
                    print(f"    国士无双: {display_tiles(all14)}")
        print()

        # ─── 计算点数 ────────────────────────────────
        print("  ── 计算结果 ──")
        r = calc.calculate(
            hand=tiles_to_string(hand_tiles),
            win_tile=win_tile.to_string(),
            is_tsumo=is_tsumo,
            is_riichi=is_riichi,
            is_double_riichi=is_double_riichi,
            is_ippatsu=is_ippatsu,
            is_dealer=ctx["is_dealer"],
            prevalent_wind=ctx["prevalent_wind"],
            seat_wind=ctx["seat_wind"],
            dora_indicators=dora_indicators,
            ura_dora_indicators=ura_dora_indicators if show_ura else None,
            is_haitei=is_haitei,
            is_houtei=is_houtei,
            is_rinshan=is_rinshan,
            is_chankan=is_chankan,
            honba=ctx["honba"],
        )

        if not r.is_valid:
            print(f"  ❌ {r.error_message}")
        else:
            # 役种
            print("  役种:")
            for name, han in r.yaku_list:
                print(f"    {name}: {han} 番")

            # 宝牌明细
            if r.dora_count > 0:
                details = []
                if r.indicator_dora_count > 0:
                    details.append(f"表{r.indicator_dora_count}")
                if r.ura_dora_count > 0:
                    details.append(f"里{r.ura_dora_count}")
                if r.red_dora_count > 0:
                    details.append(f"赤{r.red_dora_count}")
                print(f"    (宝牌构成: {' + '.join(details)} = {r.dora_count})")

            print()
            if r.name:
                print(f"  {r.name}!")
            print(f"  {r.han} 番 / {r.fu} 符")
            print(f"  总点数: {r.total_points} 点")
            print(f"  {r.payment_detail}")

        _continue_or_quit()


def _continue_or_quit():
    print()
    ans = input("  按 Enter 继续生成下一局，输入 q 退出: ").strip().lower()
    if ans in ("q", "quit", "exit"):
        print("  再见！")
        sys.exit(0)


if __name__ == "__main__":
    main()
