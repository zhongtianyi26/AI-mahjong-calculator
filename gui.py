"""
麻将计点器 — Streamlit 可视化界面
启动方式: streamlit run gui.py
"""

import streamlit as st
from collections import Counter
from typing import List, Optional

from mahjong_calculator.calculator.tiles import (
    Tile,
    TileType,
    Meld,
    MeldType,
    tiles_to_string,
)
from mahjong_calculator.calculator.parser import HandParser
from mahjong_calculator.calculator.calculator import Calculator

# 从 demo 模块复用手牌生成逻辑（无副作用，main() 受 __name__ 守卫）
from demo import (
    WIND_NAMES,
    generate_winning_hand_fast,
    generate_melds_from_hand,
    random_game_context,
    display_tile,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  页面设置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(page_title="麻将计点器", page_icon="🀄", layout="wide")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  缓存引擎实例
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_resource
def _calc():
    return Calculator()


@st.cache_resource
def _parser():
    return HandParser()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Unicode 麻将牌 emoji 映射
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_EMO: dict = {
    "1m": "\U0001f007",
    "2m": "\U0001f008",
    "3m": "\U0001f009",
    "4m": "\U0001f00a",
    "5m": "\U0001f00b",
    "6m": "\U0001f00c",
    "7m": "\U0001f00d",
    "8m": "\U0001f00e",
    "9m": "\U0001f00f",
    "0m": "\U0001f00b",
    "1s": "\U0001f010",
    "2s": "\U0001f011",
    "3s": "\U0001f012",
    "4s": "\U0001f013",
    "5s": "\U0001f014",
    "6s": "\U0001f015",
    "7s": "\U0001f016",
    "8s": "\U0001f017",
    "9s": "\U0001f018",
    "0s": "\U0001f014",
    "1p": "\U0001f019",
    "2p": "\U0001f01a",
    "3p": "\U0001f01b",
    "4p": "\U0001f01c",
    "5p": "\U0001f01d",
    "6p": "\U0001f01e",
    "7p": "\U0001f01f",
    "8p": "\U0001f020",
    "9p": "\U0001f021",
    "0p": "\U0001f01d",
    "1z": "\U0001f000",
    "2z": "\U0001f001",
    "3z": "\U0001f002",
    "4z": "\U0001f003",
    "5z": "\U0001f006",
    "6z": "\U0001f005",
    "7z": "\U0001f004\ufe0e",
}
_BACK_TILE = "\U0001f02b"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_CSS = """
<style>
.block-container{padding-top:0.5rem!important;padding-bottom:0.5rem!important}
.mj-row{display:flex;flex-wrap:wrap;gap:1px;align-items:flex-end;padding:2px 0;line-height:1}
.mj-t{
  display:inline-flex;align-items:center;justify-content:center;
  font-size:42px;line-height:1;padding:3px 5px;
  border:2px solid #bbb;border-radius:7px;
  background:#DDD;
  position:relative;cursor:default;
  box-shadow:1px 2px 4px rgba(0,0,0,.25);
}
/* 花色底色 — 饱和度足够高，深色/浅色模式都可见 */
.mj-t.man{background:#FFBB66;border-color:#BB5500}
.mj-t.pin{background:#88AAFF;border-color:#1133BB}
.mj-t.sou{background:#66CC66;border-color:#116611}
.mj-t.ji {background:#CCBBAA;border-color:#775544}
/* 宝牌：金框覆盖花色框 */
.mj-t.dora{border-color:#DAA520!important;box-shadow:0 0 7px 1px rgba(218,165,32,.6)}
.mj-t.win{border-color:#00BCD4!important;box-shadow:0 0 9px 2px rgba(0,188,212,.65)}
.mj-t.red::after{
  content:"赤";position:absolute;bottom:-2px;right:-2px;
  font-size:9px;color:#fff;background:#D32F2F;
  padding:0 2px;border-radius:2px 0 5px 0;line-height:14px;
  font-family:sans-serif;font-weight:700;
}
.mj-sep{display:inline-block;width:14px}
h4{margin:2px 0!important}
div[data-testid="stMetric"] label{font-size:13px!important}
div[data-testid="stMetric"] div[data-testid="stMetricValue"]{font-size:22px!important}
</style>
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HTML 渲染辅助
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_SUIT_CLS = {
    TileType.MANZU: "man",
    TileType.PINZU: "pin",
    TileType.SOUZU: "sou",
    TileType.JIHAI: "ji",
}


def _tile_html(tile: Tile, *, win=False, dora=False, back=False) -> str:
    if back:
        return f'<span class="mj-t ji">{_BACK_TILE}</span>'
    key = tile.to_string()
    emo_key = ("0" + key[1]) if tile.is_red else key
    emo = _EMO.get(emo_key) or _EMO.get(key, "?")
    cls = ["mj-t", _SUIT_CLS.get(tile.tile_type, "ji")]
    if dora:
        cls.append("dora")
    if win:
        cls.append("win")
    if tile.is_red:
        cls.append("red")
    return f'<span class="{" ".join(cls)}" title="{key}">{emo}</span>'


def _tiles_row(tiles: List[Tile], win_tile: Optional[Tile], dora_set: set) -> str:
    parts = [_tile_html(t, dora=(t in dora_set)) for t in tiles]
    if win_tile is not None:
        parts.append('<span class="mj-sep"></span>')
        parts.append(_tile_html(win_tile, win=True, dora=(win_tile in dora_set)))
    return f'<div class="mj-row">{"".join(parts)}</div>'


def _indicators_row(indicators: List[str]) -> str:
    parts = [_tile_html(Tile.from_string(s)) for s in indicators]
    return f'<div class="mj-row">{"".join(parts)}</div>'


def _melds_row(melds: List[Meld], dora_set: set) -> str:
    groups = []
    for m in melds:
        if m.meld_type == MeldType.ANKAN:
            g = (
                _tile_html(m.tiles[0], back=True)
                + _tile_html(m.tiles[1], dora=(m.tiles[1] in dora_set))
                + _tile_html(m.tiles[2], dora=(m.tiles[2] in dora_set))
                + _tile_html(m.tiles[3], back=True)
            )
        else:
            g = "".join(_tile_html(t, dora=(t in dora_set)) for t in m.tiles)
        groups.append(g)
    sep = '<span class="mj-sep"></span>'
    return f'<div class="mj-row">{sep.join(groups)}</div>'


def _meld_label(m: Meld) -> str:
    return {
        MeldType.CHI: "吃",
        MeldType.PON: "碰",
        MeldType.KAN: "明杠",
        MeldType.ANKAN: "暗杠",
    }.get(m.meld_type, "?")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  拆法文本
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _patterns_text(hand, win, parser, melds=None) -> str:
    patterns = parser.parse(hand, win, melds=melds)
    if not patterns:
        return "无合法拆法"
    lines = []
    for i, pat in enumerate(patterns):
        if not pat.jantou and not pat.shuntsu and not pat.koutsu:
            all14 = hand + [win]
            cnt = Counter(all14)
            kind = (
                "七对子"
                if (len(cnt) == 7 and all(v == 2 for v in cnt.values()))
                else "国士无双"
            )
            lines.append(f"拆法{i+1}: {kind}")
        else:
            parts = []
            if pat.jantou:
                parts.append(
                    f"对[{display_tile(pat.jantou[0])}{display_tile(pat.jantou[1])}]"
                )
            for s in pat.shuntsu:
                parts.append(f"顺[{''.join(display_tile(t) for t in s)}]")
            for k in pat.koutsu:
                parts.append(f"刻[{''.join(display_tile(t) for t in k)}]")
            for s in pat.open_shuntsu:
                parts.append(f"吃[{''.join(display_tile(t) for t in s)}]")
            for k in pat.open_koutsu:
                parts.append(f"碰[{''.join(display_tile(t) for t in k)}]")
            for k in pat.min_kantsu:
                parts.append(f"明杠[{display_tile(k[0])}×4]")
            for k in pat.ankan:
                parts.append(f"暗杠[{display_tile(k[0])}×4]")
            lines.append(f"拆法{i+1}:  {'  '.join(parts)}")
    return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  手牌生成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _generate():
    calc = _calc()
    parser = _parser()
    hand, win, dora, ura, mentsu = generate_winning_hand_fast(use_red_dora=True)
    ctx = random_game_context()

    st.session_state.hand = hand
    st.session_state.win = win
    st.session_state.dora = dora
    st.session_state.ura = ura
    st.session_state.ctx = ctx

    dora_tiles = {calc._get_dora_tile(d) for d in dora}
    ura_tiles = {calc._get_dora_tile(d) for d in ura}
    st.session_state.dora_set = dora_tiles | ura_tiles

    st.session_state.furo_ok = False
    try:
        fh, fw, fm = generate_melds_from_hand(hand, win, mentsu)
        if parser.parse(fh, fw, melds=fm):
            st.session_state.furo_hand = fh
            st.session_state.furo_win = fw
            st.session_state.furo_melds = fm
            st.session_state.furo_ok = True
    except Exception:
        pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  主界面
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(_CSS, unsafe_allow_html=True)

if "hand" not in st.session_state:
    _generate()

# ─── 侧边栏：条件控件 ───────────────────────────────
with st.sidebar:
    st.markdown("## 🀄 麻将计点器")
    st.button(
        "🎲 随机生成手牌", on_click=_generate, type="primary", use_container_width=True
    )
    st.divider()

    furo_ok = st.session_state.furo_ok
    if furo_ok:
        is_open_furo = any(m.is_open() for m in st.session_state.furo_melds)
        mode = st.radio("计算模式", ["门前清", "副露"], horizontal=True, key="mode")
    else:
        is_open_furo = False
        mode = "门前清"

    is_menzen = (mode == "门前清") or (furo_ok and not is_open_furo)

    st.markdown("**和了方式**")
    win_method = st.radio(
        "和了",
        ["荣和", "自摸"],
        horizontal=True,
        key="win_method",
        label_visibility="collapsed",
    )
    is_tsumo = win_method == "自摸"

    st.markdown("**立直**")
    riichi_sel = st.radio(
        "立直",
        ["无", "立直", "双立直"],
        horizontal=True,
        key="riichi",
        label_visibility="collapsed",
        disabled=not is_menzen,
    )
    riichi_val = riichi_sel if is_menzen else "无"
    has_riichi = riichi_val in ("立直", "双立直")
    ippatsu = st.checkbox("一発", key="ippatsu", disabled=not has_riichi)
    ippatsu_val = ippatsu and has_riichi

    st.markdown("**特殊条件**")
    _ca, _cb = st.columns(2)
    with _ca:
        haitei = st.checkbox("海底", key="haitei", disabled=not is_tsumo)
        rinshan = st.checkbox("岭上", key="rinshan", disabled=not is_tsumo)
    with _cb:
        houtei = st.checkbox("河底", key="houtei", disabled=is_tsumo)
        chankan = st.checkbox("抢杠", key="chankan", disabled=is_tsumo)

    haitei_v = haitei and is_tsumo
    houtei_v = houtei and not is_tsumo
    rinshan_v = rinshan and is_tsumo
    chankan_v = chankan and not is_tsumo

# ─── 组装条件 ───────────────────────────────────────
conditions: dict = {"is_tsumo": is_tsumo}
if riichi_val == "立直":
    conditions["is_riichi"] = True
elif riichi_val == "双立直":
    conditions["is_double_riichi"] = True
if ippatsu_val:
    conditions["is_ippatsu"] = True
if haitei_v:
    conditions["is_haitei"] = True
if houtei_v:
    conditions["is_houtei"] = True
if rinshan_v:
    conditions["is_rinshan"] = True
if chankan_v:
    conditions["is_chankan"] = True

# ─── 别名 ───────────────────────────────────────────
hand = st.session_state.hand
win = st.session_state.win
dora = st.session_state.dora
ura = st.session_state.ura
ctx = st.session_state.ctx
dora_set = st.session_state.dora_set

# ════════════════════════════════════════════════════
#  场况 + 宝牌（同一行三列）
# ════════════════════════════════════════════════════
_WIND_Z = {"E": "1z", "S": "2z", "W": "3z", "N": "4z"}
kan_count = len(dora) - 1
prev_tile = _tile_html(Tile.from_string(_WIND_Z[ctx["prevalent_wind"]]))
seat_tile = _tile_html(Tile.from_string(_WIND_Z[ctx["seat_wind"]]))
dealer_badge = "👑 亲家" if ctx["is_dealer"] else "🀫 子家"

st.write("")  # 增加一点空隙避免被顶部导航栏遮挡
st.write("")  # 增加一点空隙避免被顶部导航栏遮挡
st.write("")  # 增加一点空隙避免被顶部导航栏遮挡

_ci, _cd, _cu = st.columns(3)
with _ci:
    # 移除上方标题，直接显示内容以对齐
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">'
        f'<span style="font-size:13px">场风</span>{prev_tile}'
        f'<span style="font-size:13px;margin-left:4px">自风</span>{seat_tile}'
        f'<span style="font-size:13px;margin-left:6px">{dealer_badge}'
        f"&nbsp;│&nbsp;开杠&nbsp;<b>{kan_count}</b></span>"
        f"</div>",
        unsafe_allow_html=True,
    )
with _cd:
    dora_tiles_html = "".join(_tile_html(Tile.from_string(s)) for s in dora)
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">'
        f'<span style="font-size:13px;white-space:nowrap">表宝牌指示</span>'
        f"{dora_tiles_html}</div>",
        unsafe_allow_html=True,
    )
with _cu:
    ura_tiles_html = "".join(_tile_html(Tile.from_string(s)) for s in ura)
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">'
        f'<span style="font-size:13px;white-space:nowrap">里宝牌指示</span>'
        f"{ura_tiles_html}</div>",
        unsafe_allow_html=True,
    )

# ════════════════════════════════════════════════════
#  左：手牌显示  右：实时计算结果
# ════════════════════════════════════════════════════
main_col, res_col = st.columns([3, 2])

with main_col:
    st.caption("✨金边=宝牌  🔷青边=和牌  赤=赤宝")
    st.markdown(_tiles_row(sorted(hand), win, dora_set), unsafe_allow_html=True)

    with st.expander("📋 拆法"):
        st.text(_patterns_text(hand, win, _parser()))

    if furo_ok:
        melds_list = st.session_state.furo_melds
        furo_hand = st.session_state.furo_hand
        furo_win = st.session_state.furo_win
        meld_desc = "  ".join(
            f"**{_meld_label(m)}**[{''.join(display_tile(t) for t in m.tiles)}]"
            for m in melds_list
        )
        st.markdown(f"###### 副露 — {meld_desc}")
        st.markdown(_melds_row(melds_list, dora_set), unsafe_allow_html=True)
        st.caption("副露后手牌")
        st.markdown(
            _tiles_row(sorted(furo_hand), furo_win, dora_set), unsafe_allow_html=True
        )
        with st.expander("📋 副露拆法"):
            st.text(_patterns_text(furo_hand, furo_win, _parser(), melds=melds_list))

with res_col:
    # ══ 实时计算（无需点击按钮）══
    if mode == "副露" and furo_ok:
        use_hand = st.session_state.furo_hand
        use_win = st.session_state.furo_win
        use_melds = st.session_state.furo_melds
    else:
        use_hand = hand
        use_win = win
        use_melds = None

    is_riichi_flag = conditions.get("is_riichi", False) or conditions.get(
        "is_double_riichi", False
    )

    r = _calc().calculate(
        hand=tiles_to_string(use_hand),
        win_tile=use_win.to_string(),
        is_tsumo=conditions.get("is_tsumo", False),
        is_riichi=conditions.get("is_riichi", False),
        is_double_riichi=conditions.get("is_double_riichi", False),
        is_ippatsu=conditions.get("is_ippatsu", False),
        is_dealer=ctx["is_dealer"],
        prevalent_wind=ctx["prevalent_wind"],
        seat_wind=ctx["seat_wind"],
        dora_indicators=dora,
        ura_dora_indicators=ura if is_riichi_flag else None,
        is_haitei=conditions.get("is_haitei", False),
        is_houtei=conditions.get("is_houtei", False),
        is_rinshan=conditions.get("is_rinshan", False),
        is_chankan=conditions.get("is_chankan", False),
        melds=use_melds,
        honba=0,
    )

    st.markdown("#### 📊 结果")
    if not r.is_valid:
        err = r.error_message or "无役（至少需要1个役种，宝牌不算役）"
        st.error(f"❌ {err}")
    else:
        _m1, _m2, _m3 = st.columns(3)
        with _m1:
            st.metric("番", f"{r.han}番")
        with _m2:
            st.metric("符", f"{r.fu}符" if r.fu else "—")
        with _m3:
            st.metric("点数", f"{r.total_points:,}")

        if r.name:
            st.markdown(f"### 🏆 {r.name}")

        lines = []
        for name, han in r.yaku_list:
            if not name.startswith("宝牌"):
                lines.append(f"**{name}** {han}番")
        dora_parts = []
        if r.indicator_dora_count:
            dora_parts.append(f"表×{r.indicator_dora_count}")
        if r.ura_dora_count:
            dora_parts.append(f"里×{r.ura_dora_count}")
        if r.red_dora_count:
            dora_parts.append(f"赤×{r.red_dora_count}")
        if dora_parts:
            lines.append(f"✨宝牌 {' '.join(dora_parts)}")
        for line in lines:
            st.markdown(f"- {line}")

        st.divider()
        if r.is_tsumo_result:
            if r.each_pays:
                st.info(f"💰 庄家自摸  各家 **{r.each_pays:,}**")
            else:
                st.info(
                    f"💰 闲家自摸  闲 **{r.non_dealer_pays:,}** / 庄 **{r.dealer_pays:,}**"
                )
        else:
            pay = r.direct_pay if r.direct_pay else r.total_points
            st.info(f"💰 荣和  放铳 **{pay:,}**")
