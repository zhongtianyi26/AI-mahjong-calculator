# AI 日麻记点器

日本麻将计点计算器 - 纯Python实现

## 使用方法

```python
import sys
sys.path.append('c:/path/to/AI-mahjong-calculator')
from mahjong_calculator import Calculator

calc = Calculator()
result = calc.calculate(
    hand="234m456p678s5566s",  # 手牌（13张）
    win_tile="5s",              # 和牌
    is_tsumo=True,              # 自摸
    is_riichi=True,             # 立直
    dora_indicators=["4s"]      # 宝牌指示牌（5s是宝牌）
)

if result.is_valid:
    print(f"役种: {result.yaku_list}")
    print(f"番符: {result.han}番{result.fu}符")
    print(f"点数: {result.total_points}点")
```

## 牌的表示

- 万子: `1m-9m`
- 筒子: `1p-9p`  
- 索子: `1s-9s`
- 字牌: `1z`(东) `2z`(南) `3z`(西) `4z`(北) `5z`(白) `6z`(发) `7z`(中)

紧凑格式: `"123m"` = `"1m2m3m"`

## 支持的役种

完整支持30+种役种：

- **1番**: 立直、断幺九、役牌、平和、一杯口等
- **2番**: 对对和、三暗刻、三色同顺、七对子等  
- **3番**: 混一色、纯全带幺九、二杯口
- **6番**: 清一色
- **役满**: 国士无双、四暗刻、大三元、字一色等

## 测试

```bash
pip install pytest
pytest tests/
```

## 项目结构

```
AI-mahjong-calculator/
├── mahjong_calculator/    # 核心代码
│   └── calculator/
│       ├── tiles.py       # 牌的数据结构
│       ├── parser.py      # 手牌解析
│       ├── yaku.py        # 役种判断
│       ├── fu.py          # 符数计算
│       ├── points.py      # 点数计算
│       └── calculator.py  # 主计算器
└── tests/                 # 测试用例
```

详细开发文档：[DEVELOPMENT.md](DEVELOPMENT.md)
