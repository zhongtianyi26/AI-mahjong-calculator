"""
临时可视化演示脚本  随机生成可和手牌并自动计算所有场景点数
后续可直接删除此文件，不影响核心代码。
"""

import random
import sys
from collections import Counter
from typing import List, Tuple

from mahjong_calculator.calculator.tiles import (
    Tile,
    TileType,
    Meld,
    MeldType,
    tiles_to_string,
)
from mahjong_calculator.calculator.parser import HandParser
from mahjong_calculator.calculator.calculator import Calculator

#  常量
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
    "1p": "一饼",
    "2p": "二饼",
    "3p": "三饼",
    "4p": "四饼",
    "5p": "五饼",
    "6p": "六饼",
    "7p": "七饼",
    "8p": "八饼",
    "9p": "九饼",
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
    "0m": "五万",
    "0p": "五饼",
    "0s": "五索",
}

# ─── ANSI 颜色 ───────────────────────────────────────
_RESET = "\033[0m"
_RED = "\033[91m"  # 赤宝牌
_GOLD = "\033[93m"  # 宝牌命中
_CYAN = "\033[96m"  # 字牌和牌高亮
_MANZU = "\033[38;5;208m"  # 万子（橙）
_PINZU = "\033[34m"  # 饼子（蓝）
_SOUZU = "\033[32m"  # 索子（绿）
_DIM = "\033[2m"  # 暗色
_BOLD = "\033[1m"  # 加粗
_GRY = "\033[90m"  # 灰色（无效行）


#  ASCII 牌面渲染
def _display_width(s: str) -> int:
    w = 0
    for ch in s:
        cp = ord(ch)
        if (
            0x2E80 <= cp <= 0x303E
            or 0x3041 <= cp <= 0x33FF
            or 0x3400 <= cp <= 0x4DBF
            or 0x4E00 <= cp <= 0x9FFF
            or 0xAC00 <= cp <= 0xD7AF
            or 0xF900 <= cp <= 0xFAFF
            or 0xFE30 <= cp <= 0xFE6F
            or 0xFF01 <= cp <= 0xFF60
            or 0xFFE0 <= cp <= 0xFFE6
            or 0x20000 <= cp <= 0x2FA1F
        ):
            w += 2
        else:
            w += 1
    return w


def _pad_center(s: str, width: int) -> str:
    cur = _display_width(s)
    if cur >= width:
        return s
    total = width - cur
    left = total // 2
    return " " * left + s + " " * (total - left)


def render_tile_visual(
    tile: Tile, highlight: bool = False, color_code: str = ""
) -> List[str]:
    face = TILE_DISPLAY.get(tile.to_string(), tile.to_string())
    face = face[:2] if len(face) > 2 else face
    inner = _pad_center(face, 4)
    top = "╔════╗" if highlight else "┌────┐"
    bot = "╚════╝" if highlight else "└────┘"
    side = "║" if highlight else "│"
    if color_code:
        r = _RESET
        return [
            f"{color_code}{top}{r}",
            f"{color_code}{side}{inner}{side}{r}",
            f"{color_code}{bot}{r}",
        ]
    return [top, f"{side}{inner}{side}", bot]


def render_tiles_visual(
    tiles: List[Tile], per_line: int = 7, highlight_last: bool = False
) -> str:
    if not tiles:
        return ""
    lines: List[str] = []
    for i in range(0, len(tiles), per_line):
        chunk = tiles[i : i + per_line]
        hi_flags = [False] * len(chunk)
        if highlight_last and i + per_line >= len(tiles):
            hi_flags[-1] = True
        tile_rows = [render_tile_visual(t, hi_flags[j]) for j, t in enumerate(chunk)]
        for row_idx in range(3):
            lines.append(" ".join(tr[row_idx] for tr in tile_rows))
    return "\n".join(lines)


def render_hand_and_win(
    hand: List[Tile], win_tile: Tile, dora_tiles: set = None
) -> str:
    """手牌 13 张 + 分隔符 + 和牌 1 张，全部在同一行显示。
    dora_tiles: 宝牌实际牌面集合（由宝牌指示牌推算），用于着色。
    赤宝牌 → 红色，普通宝牌命中 → 金色，和牌双边框 → 青色。
    """
    dora_set = dora_tiles or set()

    def _suit_color(t: Tile) -> str:
        if t.tile_type == TileType.MANZU:
            return _MANZU
        if t.tile_type == TileType.PINZU:
            return _PINZU
        if t.tile_type == TileType.SOUZU:
            return _SOUZU
        return ""

    def tile_color(t: Tile) -> str:
        if t.is_red:
            return _RED
        if t in dora_set:
            return _GOLD
        return _suit_color(t)  # 字牌返回 ""

    hand_rows = [
        render_tile_visual(t, highlight=False, color_code=tile_color(t)) for t in hand
    ]
    wc = tile_color(win_tile)
    win_color = wc if wc else _CYAN  # 字牌和牌 fallback 青色
    win_rows = [render_tile_visual(win_tile, highlight=True, color_code=win_color)]
    sep = ["  ", "  ", "  "]  # 3 行分隔符
    all_cols = hand_rows + [sep] + win_rows
    lines = []
    for row_idx in range(3):
        lines.append(" ".join(col[row_idx] for col in all_cols))
    return "\n".join(lines)


def display_tile(tile: Tile) -> str:
    return TILE_DISPLAY.get(tile.to_string(), tile.to_string())


def render_indicator_row(
    indicators: List[str], calc: Calculator, label: str = "宝牌指示牌"
) -> str:
    """将宝牌指示牌以可视化牌面渲染成单行（3行ASCII），附带标签。"""
    ind_tiles = [Tile.from_string(s) for s in indicators]

    def _suit_color(t: Tile) -> str:
        if t.tile_type == TileType.MANZU:
            return _MANZU
        if t.tile_type == TileType.PINZU:
            return _PINZU
        if t.tile_type == TileType.SOUZU:
            return _SOUZU
        return ""

    cols = [
        render_tile_visual(t, highlight=False, color_code=_suit_color(t))
        for t in ind_tiles
    ]
    lines = []
    for row in range(3):
        lines.append("  " + " ".join(c[row] for c in cols))
    return "\n".join(lines)


def render_tile_back() -> List[str]:
    """渲染牌背（暗杠中间两张用）"""
    return [
        f"{_DIM}┌────┐{_RESET}",
        f"{_DIM}│████│{_RESET}",
        f"{_DIM}└────┘{_RESET}",
    ]


def render_meld_row(melds_list: List[Meld], dora_set: set = None) -> str:
    """将副露以可视化牌面渲染成单行（3行ASCII），各副露间用空白分隔。
    暗杠：中间两张翻过去显示为牌背。"""
    if not melds_list:
        return ""

    _dora = dora_set or set()

    def _suit_color(t: Tile) -> str:
        if t.tile_type == TileType.MANZU:
            return _MANZU
        if t.tile_type == TileType.PINZU:
            return _PINZU
        if t.tile_type == TileType.SOUZU:
            return _SOUZU
        return ""

    def _tile_color(t: Tile) -> str:
        if t.is_red:
            return _RED
        if t in _dora:
            return _GOLD
        return _suit_color(t)

    groups: List[List[List[str]]] = []
    for m in melds_list:
        if m.meld_type == MeldType.ANKAN:
            # 暗杠：两侧牌背，中间两张正面
            tile_cols = [
                render_tile_back(),
                render_tile_visual(
                    m.tiles[1], highlight=False, color_code=_tile_color(m.tiles[1])
                ),
                render_tile_visual(
                    m.tiles[2], highlight=False, color_code=_tile_color(m.tiles[2])
                ),
                render_tile_back(),
            ]
        else:
            tile_cols = [
                render_tile_visual(t, highlight=False, color_code=_tile_color(t))
                for t in m.tiles
            ]
        groups.append(tile_cols)

    lines = []
    for row in range(3):
        parts = []
        for g in groups:
            parts.append(" ".join(c[row] for c in g))
        lines.append("  " + "   ".join(parts))
    return "\n".join(lines)


#  从构造好的面子结构中生成合法副露
def generate_melds_from_hand(
    hand: List[Tile], win_tile: Tile, mentsu_keys: list
) -> Tuple[List[Tile], Tile, List[Meld]]:
    """
    从已知四面子结构中随机将1~2个面子转为副露(吃/碰/明杠/暗杠)。
    刻子有约10%几率升级为杠（需第4张可用）。
    返回 (新手牌, 和牌, 副露列表)。
    """
    n_furo = random.randint(1, min(2, len(mentsu_keys)))
    indices = random.sample(range(len(mentsu_keys)), n_furo)
    furo_melds: List[Meld] = []

    all14 = list(hand) + [win_tile]
    remaining = list(all14)
    tile_counts = Counter((t.value, t.tile_type) for t in all14)

    def _extract(remaining_list, value, tile_type):
        """从 remaining 中取出一张匹配的实际牌（保留赤宝状态）"""
        for i, r in enumerate(remaining_list):
            if r.value == value and r.tile_type == tile_type:
                return remaining_list.pop(i)
        return None

    for idx in indices:
        keys = mentsu_keys[idx]
        if keys[0] == keys[1]:
            # 刻子
            tile_key = keys[0]  # (value, tile_type)
            gang = 1  # ~10% 几率升级为杠（第4张牌必须可用：手里只有3张）
            if random.random() < gang and tile_counts[tile_key] < 4:
                extracted = [
                    _extract(remaining, tile_key[0], tile_key[1]) for _ in range(3)
                ]
                extracted = [t for t in extracted if t is not None]
                # 第4张：合成（不在手里，视为从牌山摸来）
                extracted.append(Tile(tile_key[0], tile_key[1]))
                meld_type = random.choice([MeldType.KAN, MeldType.ANKAN])
                furo_melds.append(Meld(meld_type, extracted))
            else:
                # 碰
                extracted = [
                    _extract(remaining, tile_key[0], tile_key[1]) for _ in range(3)
                ]
                extracted = [t for t in extracted if t is not None]
                furo_melds.append(Meld(MeldType.PON, extracted))
        else:
            # 顺子 → 吃
            extracted = [_extract(remaining, k[0], k[1]) for k in keys]
            extracted = [t for t in extracted if t is not None]
            furo_melds.append(Meld(MeldType.CHI, extracted))

    # 和牌从剩余中随机取一张
    random.shuffle(remaining)
    new_win = remaining[-1]
    new_hand = remaining[:-1]
    return new_hand, new_win, furo_melds


ALL_NUM_TILES = [
    (v, t)
    for t in [TileType.MANZU, TileType.PINZU, TileType.SOUZU]
    for v in range(1, 10)
] + [(v, TileType.JIHAI) for v in range(1, 8)]
SHUNTSU_STARTS = [
    (v, s)
    for s in [TileType.MANZU, TileType.PINZU, TileType.SOUZU]
    for v in range(1, 8)
]


def generate_winning_hand_fast(
    use_red_dora: bool = True,
) -> Tuple[List[Tile], Tile, List[str], List[str], list]:
    """直接构造合法和牌：随机雀头 + 4 面子，即建即得，成功率接近100%
    返回: (hand, win_tile, dora_indicators, ura_indicators, mentsu_keys)
    mentsu_keys 用于后续生成副露变体。
    """
    parser = HandParser()

    while True:
        counts: Counter = Counter()

        jv, jt = random.choice(ALL_NUM_TILES)
        counts[(jv, jt)] += 2
        if counts[(jv, jt)] > 4:
            continue

        melds = []
        ok = True
        for _ in range(4):
            use_shuntsu = (jt == TileType.JIHAI) or random.random() < 0.65
            if use_shuntsu:
                sv, st = random.choice(SHUNTSU_STARTS)
                keys = [(sv, st), (sv + 1, st), (sv + 2, st)]
                for k in keys:
                    counts[k] += 1
                    if counts[k] > 4:
                        ok = False
                        break
                if not ok:
                    break
                melds.append(keys)
            else:
                kv, kt = random.choice(ALL_NUM_TILES)
                counts[(kv, kt)] += 3
                if counts[(kv, kt)] > 4:
                    ok = False
                    break
                melds.append([(kv, kt)] * 3)
        if not ok:
            continue

        # 每花色赤五限1张
        red_used: Counter = Counter()

        def make_tile(v: int, t: TileType) -> Tile:
            if (
                use_red_dora
                and v == 5
                and t != TileType.JIHAI
                and red_used[t] == 0
                and random.random() < 0.25
            ):
                red_used[t] += 1
                return Tile(5, t, is_red=True)
            return Tile(v, t)

        all14: List[Tile] = [make_tile(jv, jt), make_tile(jv, jt)]
        for keys in melds:
            for kv, kt in keys:
                all14.append(make_tile(kv, kt))

        random.shuffle(all14)
        win_idx = random.randrange(14)
        hand = [t for i, t in enumerate(all14) if i != win_idx]
        win = all14[win_idx]

        if not parser.parse(hand, win):
            continue

        # 从逻辑牌库中抽宝牌指示牌
        pool = [Tile(v, t) for v, t in ALL_NUM_TILES]
        random.shuffle(pool)
        kan_count = random.choices([0, 1], weights=[3, 1])[0]
        n = 1 + kan_count
        dora_ind = [t.to_string() for t in pool[:n]]
        ura_ind = [t.to_string() for t in pool[n : n * 2]]
        return hand, win, dora_ind, ura_ind, melds


#  随机场况（场风只有东/南，去掉本场）
def random_game_context() -> dict:
    prevalent = random.choice(["E", "S"])
    seat = random.choice(WIND_LIST)
    return {
        "prevalent_wind": prevalent,
        "seat_wind": seat,
        "is_dealer": seat == "E",
    }


#  交互式条件选择 → 单次计算
CONDITION_MENU = [
    # (键, 显示名, kwarg键, 值, 互斥组, 需门清)
    ("1", "自摸", "is_tsumo", True, "win", False),
    ("2", "荣和", "is_tsumo", False, "win", False),
    ("3", "立直", "is_riichi", True, "riichi", True),
    ("4", "双立直", "is_double_riichi", True, "riichi", True),
    ("5", "一发", "is_ippatsu", True, None, True),
    ("6", "海底", "is_haitei", True, "bottom", False),
    ("7", "河底", "is_houtei", True, "bottom", False),
    ("8", "岭上", "is_rinshan", True, "special", False),
    ("9", "抢杠", "is_chankan", True, "special", False),
]

# 自动冲突检测规则
_CONFLICT_RULES = {
    # 海底→必须自摸, 河底→必须荣和
    "is_haitei": {"requires": {"is_tsumo": True}},
    "is_houtei": {"requires": {"is_tsumo": False}},
    # 岭上→必须自摸, 抢杠→必须荣和
    "is_rinshan": {"requires": {"is_tsumo": True}},
    "is_chankan": {"requires": {"is_tsumo": False}},
    # 一发→需要立直或双立直
    "is_ippatsu": {"requires_any": ["is_riichi", "is_double_riichi"]},
}


def _prompt_conditions(is_menzen: bool) -> dict:
    """交互式显示条件菜单，返回 kwargs dict。"""
    selected: dict = {}  # kwarg_key -> value
    group_selected: dict = {}  # group -> kwarg_key

    print(f"\n  {_BOLD}── 选择和牌条件 ──{_RESET}")
    print(f"  输入编号切换(可多选，空格/逗号分隔)，直接回车=荣和(无特殊条件)")

    # 显示菜单
    for key, name, kwarg, val, group, need_menzen in CONDITION_MENU:
        disabled = need_menzen and not is_menzen
        status = f" {_GRY}(需门清){_RESET}" if disabled else ""
        print(f"    {key}. {name}{status}")

    ans = input("  选择: ").strip()
    if not ans:
        return {"is_tsumo": False}  # 默认荣和

    choices = set()
    for ch in ans.replace(",", " ").replace("，", " ").split():
        choices.add(ch.strip())

    for key, name, kwarg, val, group, need_menzen in CONDITION_MENU:
        if key in choices:
            if need_menzen and not is_menzen:
                print(f"    {_GRY}⚠ {name} 需要门清，已跳过{_RESET}")
                continue
            # 互斥组检查
            if group and group in group_selected:
                old_key = group_selected[group]
                print(f"    {_GRY}⚠ {name} 与已选条件互斥，已跳过{_RESET}")
                continue
            selected[kwarg] = val
            if group:
                group_selected[group] = kwarg

    # 默认自摸/荣和
    if "is_tsumo" not in selected:
        selected["is_tsumo"] = False

    # 冲突自动修正
    for kwarg, rule in _CONFLICT_RULES.items():
        if kwarg not in selected:
            continue
        if "requires" in rule:
            for rk, rv in rule["requires"].items():
                if selected.get(rk) is not None and selected[rk] != rv:
                    req_name = "自摸" if rv else "荣和"
                    print(
                        f"    {_GOLD}⚠ 自动切换为{req_name}（因选了相关条件）{_RESET}"
                    )
                selected[rk] = rv
        if "requires_any" in rule:
            if not any(selected.get(k) for k in rule["requires_any"]):
                print(f"    {_GRY}⚠ 一发需要立直/双立直，已移除一发{_RESET}")
                del selected[kwarg]

    return selected


def compute_single(
    calc: Calculator,
    hand: List[Tile],
    win_tile: Tile,
    ctx: dict,
    dora_indicators: List[str],
    ura_dora_indicators: List[str],
    melds: List[Meld] = None,
    conditions: dict = None,
) -> dict:
    """根据用户选择的条件做单次计算"""
    cond = conditions or {"is_tsumo": False}
    is_riichi = cond.get("is_riichi", False) or cond.get("is_double_riichi", False)

    kwargs = dict(
        hand=tiles_to_string(hand),
        win_tile=win_tile.to_string(),
        is_tsumo=cond.get("is_tsumo", False),
        is_riichi=cond.get("is_riichi", False),
        is_double_riichi=cond.get("is_double_riichi", False),
        is_ippatsu=cond.get("is_ippatsu", False),
        is_dealer=ctx["is_dealer"],
        prevalent_wind=ctx["prevalent_wind"],
        seat_wind=ctx["seat_wind"],
        dora_indicators=dora_indicators,
        ura_dora_indicators=ura_dora_indicators if is_riichi else None,
        is_haitei=cond.get("is_haitei", False),
        is_houtei=cond.get("is_houtei", False),
        is_rinshan=cond.get("is_rinshan", False),
        is_chankan=cond.get("is_chankan", False),
        melds=melds,
        honba=0,
    )
    r = calc.calculate(**kwargs)

    # 组装显示标签
    parts = []
    if cond.get("is_double_riichi"):
        parts.append("双立直")
    elif cond.get("is_riichi"):
        parts.append("立直")
    if cond.get("is_ippatsu"):
        parts.append("一发")
    if cond.get("is_tsumo"):
        parts.append("自摸")
    else:
        parts.append("荣和")
    if cond.get("is_haitei"):
        parts.append("海底")
    if cond.get("is_houtei"):
        parts.append("河底")
    if cond.get("is_rinshan"):
        parts.append("岭上")
    if cond.get("is_chankan"):
        parts.append("抢杠")
    label = "+".join(parts) if parts else "荣和"

    return {"label": label, "result": r}


#  结果表格输出
def _w(s: str, width: int) -> str:
    cur = _display_width(s)
    return s + " " * max(0, width - cur)


def show_single_result(item: dict, section_title: str = ""):
    """显示单次计算结果"""
    BD = f"{_DIM}│{_RESET}"
    label = item["label"]
    r = item["result"]

    if section_title:
        print(f"\n  {_BOLD}━━ {section_title}: {label} ━━{_RESET}")
    else:
        print(f"\n  {_BOLD}━━ {label} ━━{_RESET}")

    if not r.is_valid:
        err = r.error_message or "无役"
        print(f"  {_GRY}✗ {err}{_RESET}")
        return

    # 役种
    yaku_parts = [f"{n}({h}番)" for n, h in r.yaku_list if not n.startswith("宝牌")]
    dp = []
    if r.indicator_dora_count:
        dp.append(f"表{r.indicator_dora_count}")
    if r.ura_dora_count:
        dp.append(f"里{r.ura_dora_count}")
    if r.red_dora_count:
        dp.append(f"赤{r.red_dora_count}")
    dora_str = f" {_GOLD}+宝[{'+'.join(dp)}]{_RESET}" if dp else ""
    tag_str = f"{_BOLD}【{r.name}】{_RESET} " if r.name else ""

    fu_str = f"{r.fu}符" if r.fu else ""
    print(
        f"  {_BOLD}{r.han}番{_RESET} {fu_str}  {tag_str}{' '.join(yaku_parts)}{dora_str}"
    )
    print(f"  {_BOLD}点数: {r.total_points}{_RESET}")

    if r.is_tsumo_result:
        if r.each_pays:
            print(f"  支付: {r.each_pays} all")
        else:
            print(f"  支付: 闲家各{r.non_dealer_pays} / 庄家{r.dealer_pays}")
    else:
        pay = r.direct_pay if r.direct_pay else r.total_points
        print(f"  支付: 放铳者 {pay}")


#  拆法展示
def show_patterns(
    hand: List[Tile], win_tile: Tile, parser: HandParser, melds: List[Meld] = None
):
    patterns = parser.parse(hand, win_tile, melds=melds)
    if not patterns:
        print("   无合法拆法")
        return
    all14 = hand + [win_tile]
    for i, pat in enumerate(patterns):
        if not pat.jantou and not pat.shuntsu and not pat.koutsu:
            cnt = Counter(all14)
            kind = (
                "七对子"
                if (len(cnt) == 7 and all(v == 2 for v in cnt.values()))
                else "国士无双"
            )
            print(f"  拆法{i+1}: {kind}")
        else:
            parts = []
            if pat.jantou:
                parts.append(
                    f"对[{display_tile(pat.jantou[0])}{display_tile(pat.jantou[1])}]"
                )
            for s in pat.shuntsu:
                parts.append(
                    f"顺[{display_tile(s[0])}{display_tile(s[1])}{display_tile(s[2])}]"
                )
            for k in pat.koutsu:
                parts.append(
                    f"刻[{display_tile(k[0])}{display_tile(k[1])}{display_tile(k[2])}]"
                )
            for s in pat.open_shuntsu:
                parts.append(
                    f"吃[{display_tile(s[0])}{display_tile(s[1])}{display_tile(s[2])}]"
                )
            for k in pat.open_koutsu:
                parts.append(
                    f"碰[{display_tile(k[0])}{display_tile(k[1])}{display_tile(k[2])}]"
                )
            for k in pat.min_kantsu:
                parts.append(f"明杠[{display_tile(k[0])}×4]")
            for k in pat.ankan:
                parts.append(f"暗杠[{display_tile(k[0])}×4]")
            print(f"  拆法{i+1}: " + "  ".join(parts))


def _meld_type_label(m: Meld) -> str:
    labels = {
        MeldType.CHI: "吃",
        MeldType.PON: "碰",
        MeldType.KAN: "明杠",
        MeldType.ANKAN: "暗杠",
    }
    return labels.get(m.meld_type, "?")


#  主流程
def main():
    print("=" * 70)
    print("  麻将计点可视化演示  (临时脚本，可直接删除)")
    print("  生成手牌 → 选择条件 → 计算点数")
    print("  [Enter]继续  [v]查看拆法  [q]退出")
    print("=" * 70)

    calc = Calculator()
    parser = HandParser()

    while True:
        hand_tiles, win_tile, dora_indicators, ura_dora_indicators, mentsu_keys = (
            generate_winning_hand_fast(use_red_dora=True)
        )
        ctx = random_game_context()

        # ── 场况信息 ──
        dealer_str = "亲家(庄)" if ctx["is_dealer"] else "子家(闲)"
        kan_count = len(dora_indicators) - 1

        print(f"\n{'═'*70}")
        print(
            f"  {WIND_NAMES[ctx['prevalent_wind']]}风场  "
            f"自风:{WIND_NAMES[ctx['seat_wind']]}  {dealer_str}  "
            f"开杠:{kan_count}"
        )

        # ── 宝牌指示牌 ──
        print(f"  表宝牌指示牌 ({len(dora_indicators)}枚):")
        print(render_indicator_row(dora_indicators, calc, "表宝牌指示牌"))
        print(f"  里宝牌指示牌 ({len(ura_dora_indicators)}枚):")
        print(render_indicator_row(ura_dora_indicators, calc, "里宝牌指示牌"))

        # ── 手牌渲染 ──
        dora_tiles_set = {calc._get_dora_tile(ind) for ind in dora_indicators}
        ura_tiles_set = {calc._get_dora_tile(ind) for ind in ura_dora_indicators}
        all_dora_set = dora_tiles_set | ura_tiles_set
        print("  手牌 (万=橙  饼=蓝  索=绿  金=宝牌  亮红=赤  青=和牌):")
        print(render_hand_and_win(sorted(hand_tiles), win_tile, all_dora_set))

        # ── 生成副露变体 ──
        furo_hand, furo_win, furo_melds = [], win_tile, []
        furo_ok = False
        try:
            furo_hand, furo_win, furo_melds = generate_melds_from_hand(
                hand_tiles, win_tile, mentsu_keys
            )
            if parser.parse(furo_hand, furo_win, melds=furo_melds):
                furo_ok = True
                meld_desc = "  ".join(
                    f"{_meld_type_label(m)}[{''.join(display_tile(t) for t in m.tiles)}]"
                    for m in furo_melds
                )
                print(f"\n  副露: {meld_desc}")
                print(render_meld_row(furo_melds, all_dora_set))
                print("  副露后手牌:")
                print(render_hand_and_win(sorted(furo_hand), furo_win, all_dora_set))
        except Exception as e:
            print(f"\n  {_GRY}(副露生成失败: {e}){_RESET}")

        # ── 判断门清/副露 ──
        is_furo = furo_ok and any(m.is_open() for m in furo_melds)
        only_ankan = (
            furo_ok
            and not is_furo
            and any(m.meld_type == MeldType.ANKAN for m in furo_melds)
        )

        # ── 循环选择条件计算 ──
        while True:
            print(f"\n  {'─'*40}")
            if furo_ok:
                mode_choice = (
                    input("  计算哪种？ [1]门清  [2]副露  [n]换牌  [v]拆法  [q]退出: ")
                    .strip()
                    .lower()
                )
            else:
                mode_choice = (
                    input("  [Enter]选条件计算  [n]换牌  [v]拆法  [q]退出: ")
                    .strip()
                    .lower()
                )

            if mode_choice in ("q", "quit", "exit"):
                print("  再见！")
                sys.exit(0)
            if mode_choice == "n":
                break  # 换牌
            if mode_choice == "v":
                print("  ── 门清拆法 ──")
                show_patterns(hand_tiles, win_tile, parser)
                if furo_ok and furo_melds:
                    print("  ── 副露拆法 ──")
                    show_patterns(furo_hand, furo_win, parser, melds=furo_melds)
                continue

            # 确定使用的手牌
            if mode_choice == "2" and furo_ok:
                use_hand, use_win, use_melds = furo_hand, furo_win, furo_melds
                is_menzen = not is_furo
                section = "副露"
            elif mode_choice == "1" or (not furo_ok and mode_choice in ("", "1")):
                use_hand, use_win, use_melds = hand_tiles, win_tile, None
                is_menzen = True
                section = "门前清"
            else:
                continue

            # 选择条件
            conditions = _prompt_conditions(is_menzen)

            result = compute_single(
                calc,
                use_hand,
                use_win,
                ctx,
                dora_indicators,
                ura_dora_indicators,
                melds=use_melds,
                conditions=conditions,
            )
            show_single_result(result, section_title=section)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n  再见！")
