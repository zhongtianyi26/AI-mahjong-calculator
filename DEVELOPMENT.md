# AI 日麻记点器 - 开发指南

## 项目目标

开发一个智能日本麻将辅助工具，分三期实现：

**第一期：核心算法实现**
1. 图片识别算法 - 深度学习识别麻将牌型
2. 计点算法 - 自动计算役种、番数和点数
3. 提供 Python API 接口供后续应用调用
4. 本地化运行，无需云端支持
5. **不开发 GUI 界面**，专注算法实现

**第二期：iOS/安卓移动应用**
1. 开发原生iOS和安卓应用
2. 集成第一期的识别和计点算法
3. 添加语音播报功能
4. 发布到 App Store 和 Google Play

**第三期：微信小程序**
1. 开发微信小程序版本
2. 云端部署识别和计点服务
3. 语音播报功能
4. 发布到微信小程序平台

**核心原则**：算法先行，逐步推进，本地优先。

---

## 技术栈

### 第一期（核心算法）
- **语言**：Python 3.8+
- **AI框架**：PyTorch（训练）/ ONNX Runtime（推理）
- **图像处理**：OpenCV、Pillow
- **测试**：pytest
- **打包**：作为 Python 包发布（wheel）

### 第二期（移动端 App）
- **iOS**：Swift + SwiftUI / Objective-C + UIKit
- **Android**：Kotlin + Jetpack Compose / Java
- **跨平台方案**：React Native / Flutter（可选）
- **语音合成**：iOS AVSpeechSynthesizer / Android TextToSpeech
- **算法集成**：调用第一期 Python 包或重写为原生代码

### 第三期（微信小程序）
- **前端**：微信小程序原生框架（WXML + WXSS + JS）
- **后端**：Flask / FastAPI + 微信云开发
- **语音合成**：微信 TTS API / 第三方服务（百度、讯飞）
- **部署**：阿里云 / 腾讯云 / 微信云开发

---

## 第一期：核心算法实现 ⭐ **当前阶段**

**目标**：实现图片识别和计点的核心算法，提供 Python API 接口，**不做任何 GUI**。

### 识别策略和用户交互设计

#### 问题分析

麻将计点需要以下信息：
1. ✅ **可通过拍照识别**：手牌（14张）、宝牌指示牌
2. ❌ **难以通过拍照识别**：自摸/荣和、立直、一发、本场数、里宝、场风、自风等

#### 解决方案：分阶段输入模式（推荐设计）

**你的想法非常好！** 这正是最符合真实游戏流程的设计。让我展开和优化：

**核心理念**：
1. 首先：快速判断**"你是自摸还是荣和"**（最关键的分支，3秒内）
2. 其次：拍照识别**手牌和宝牌**（需要15-20秒）
3. 最后：追加特殊情况（可选，5-10秒）

**设计特点对比**：

| 角度 | 你的设计 | 优化建议 |
|------|--------|--------|
| **首屏简洁** | ✅ 仅显示常用按钮 | ✅ 保持不变 |
| **流程时长** | ✅ 大多数<30s | ✅ 符合游戏节奏 |
| **错误恢复** | ✅ 拍错可重新拍 | ✅ 保留"重新拍照"按钮 |
| **特殊役处理** | ✅ 后续追加 | ✅ 增加一发/岭上等高频役 |
| **本场处理** | 建议添加 | ✅ 在"追加"阶段单独输入 |
| **流局处理** | ✅ 快捷按钮 | ✅ 保持不变 |
| **语音播报** | 建议添加 | ✅ 在显示结果后自动播报 |

**具体改进建议**：

1. **首屏按钮分组**（增加可读性）
   ```
   常用（最常见）：自摸 / 荣和
   带副露：吃/碰/杠
   ───────────────
   特殊结局：流局-满贯 / 流局-九种九牌
   ───────────────
   特殊开局：双立直 / 立直
   ```

2. **拍照识别流程微调**
   - 第1步拍手牌时，增加"点击标记和牌"功能
   - 第2步拍宝牌前，提示"没有宝牌？可点跳过"
   - 识别失败时允许手动输入底牌

3. **结果展示优化**
   ```
   显示顺序：役种 → 番符 → 点数分配
   
   自摸时：
   - 你获得：2000点
   - 各家支付：东500/南500/西500
   
   荣和时：
   - 放铳者支付：8000点
   - 你获得：8000点
   ```

4. **追加役的逻辑**
   - 只显示"当前合法"的役（例：没自摸就不显示岭上）
   - 勾选里宝自动检测立直状态
   - 本场数影响最终点数（显示变化前后）

5. **语音播报文案**
   ```
   "断幺九一番、役牌一番，共2番30符。
    子家荣和，放铳者支付2000点。"
   
   "立直自摸!
    加上断幺九，共2番30符，自摸2000点。"
   
   "流局・满贯!
    本家获得3000点。"
   ```


**用户体验数据对标**：

| 场景 | 操作步骤 | 预计耗时 | 体验 |
|------|--------|--------|------|
| 普通和牌 | 1按钮 + 2拍照 | <25s | ⭐⭐⭐⭐⭐ |
| 立直和牌 | 1按钮 + 2拍照 | <25s | ⭐⭐⭐⭐⭐ |
| 有特殊役 | 上述 + 2点击 + 重算 | <40s | ⭐⭐⭐⭐ |
| 流局 | 1按钮 + 1选择 | <5s | ⭐⭐⭐⭐⭐ |
| 本场 | 上述 + 数字输入 | +5s | ⭐⭐⭐⭐ |

**总体评价**：

你的设计思路 **非常符合实际应用**，相比我之前的复杂建议：
- ✅ **更快速**：普通场景3秒快速判断 + 20秒拍照
- ✅ **更专注**：一次一件事，不会信息过载
- ✅ **更容错**：逐步输入，有误可及时改正
- ✅ **更游戏化**：符合真实游戏中快速报点的节奏


#### 推荐的识别流程（二期/三期用户体验设计）

**核心理念**：快速常见场景 + 灵活追加特殊役

**流程设计**：

**阶段1：快速输入（3-5秒）**
```
首页 → 
┌─ [自摸] 
├─ [荣和]
├─ [吃/碰/杠] 
├─ [流局]: [满贯] [九种九牌]
├─ [双立直]
└─ [立直]
```
- 最常见的几个按钮，直接点击
- 流局、双立直、立直支持快速选择
- 用户需要~2-3秒就能点击

**阶段2：拍照识别（如果需要计算点数）**
- 如果点了非流局按钮，进入：

**第2a步：识别手牌和和牌**
```
┌──────────────────────────────────────┐
│ 🎥 请拍您的14张手牌（一排排列）      │
│                                      │
│ 💡 将和牌放在最右边，其他牌排一排   │
│    移动手机调整角度，让所有牌清晰   │
│                                      │
│ ┌────────────────────────────────┐  │
│ │[🖼️ 已识别]                     │  │
│ │ 1m 2m 3m 4p 5p 6p 7s 8s 9s   │  │
│ │ 1z 1z 2z 2z │ 3z            │  │
│ │ ←──手牌──→ │ ← 和牌         │  │
│ │                                │  │
│ └────────────────────────────────┘  │
│                                      │
│ ✓ 自动检测到和牌：3z               │
│   (点击修改)                        │
│                                      │
│ [重新拍照]  [确认]                 │
└──────────────────────────────────────┘
```

**第2b步：识别宝牌指示牌**
```
┌──────────────────────────────────────┐
│ 🎥 请拍宝牌区域                      │
│                                      │
│ 💡 将所有宝牌指示牌放在一起拍摄     │
│    （包括：宝牌、杠后宝牌、里宝）   │
│    移动手机调整角度，让所有牌清晰   │
│                                      │
│ ┌────────────────────────────────┐  │
│ │[🖼️ 已识别]                     │  │
│ │                                │  │
│ │ 检测到 4 个宝牌指示牌：        │  │
│ │ 1z  2m  3p  4s                │  │
│ │                                │  │
│ │ [修改]                         │  │
│ └────────────────────────────────┘  │
│                                      │
│ ─────────────────────────────────── │
│ 或手动输入宝牌数量：                │
│                                      │
│ 宝牌总数：[4] (下拉或加减按钮)     │
│                                      │
│ [重新拍照]  [跳过]  [确认]         │
└──────────────────────────────────────┘
```


**阶段3：显示初步结果**
```
┌──────────────────┐
│  断幺九 + 役牌   │  （自动检测的役）
│  2番30符         │
│  2000点          │
├──────────────────┤
│ [追加其他役]     │  ← 新增特殊役
└──────────────────┘
```

**阶段4：追加特殊役（可选）**
- 用户可点击"追加其他役"，出现：
```
□ 一发
□ 岭上开花
□ 海底捞月
□ 河底捞鱼
□ 抢杠
□ 本场数: [输入框]
```
- 选择后重新计算点数


#### API 接口设计

```python
# 识别API（优化版本）
from mahjong_calculator import Recognizer

recognizer = Recognizer(model_path="models/mahjong_v1.onnx")

# 方法1：识别手牌和和牌（将和牌放最右边，移动手机调整拍摄角度）
hand_result = recognizer.recognize_hand(
    image_path="hand_photo.jpg",
    extract_win_tile_from_right=True,  # 自动提取最右边为和牌
)

# 返回结果
print(hand_result.hand_tiles)      # ["1m", "2m", "3m", ...]（手牌部分，不含和牌）
print(hand_result.win_tile)        # "3z"（和牌，最右边自动识别）
print(hand_result.all_tiles)       # ["1m", "2m", ..., "3z"]（全部14张）
print(hand_result.sorted_hand)     # "123m456p789s1122z"（排序后手牌）
print(hand_result.confidence)      # 每张牌的置信度

# 方法2：识别所有宝牌指示牌（统一识别，无需区分宝牌/杠宝/里宝）
# 用户将所有宝牌指示牌放在一起拍照
dora_result = recognizer.recognize_dora_indicators(
    image_path="dora_area_photo.jpg",
)

# 返回结果
print(dora_result.indicators)           # ["1z", "2m", "3p", "4s"]（所有宝牌指示牌）
print(dora_result.actual_dora_tiles)    # ["2z", "3m", "4p", "5s"]（对应的实际宝牌）
print(dora_result.total_count)          # 4（宝牌总数）
print(dora_result.confidence)           # 识别置信度

# 方法3：快速手动输入宝牌数量（比拍照更快）
# 用户可以直接输入宝牌总数
dora_result = recognizer.recognize_dora_from_count(
    total_dora_count=4,  # 用户输入所有宝牌的总数量
)

# 完整使用示例：识别并计算
from mahjong_calculator import Recognizer, Calculator

# 步骤1：拍照识别手牌和和牌（将和牌放最右边）
recognizer = Recognizer(model_path="models/mahjong_v1.onnx")
hand_result = recognizer.recognize_hand("my_hand.jpg", extract_win_tile_from_right=True)
# 返回：hand_tiles=[...], win_tile="3z"

# 步骤2a：拍照识别所有宝牌指示牌（推荐，一张照片完成）
dora_result = recognizer.recognize_dora_indicators("dora_area.jpg")
# 或步骤2b：快速手动输入（如果无宝牌或用户更快）
# dora_result = recognizer.recognize_dora_from_count(total_dora_count=4)

# 步骤3：计算点数
calc = Calculator()
result = calc.calculate(
    hand=",".join(hand_result.hand_tiles),    # 手牌（不包含和牌）
    win_tile=hand_result.win_tile,            # 和牌（自动识别）
    is_tsumo=True,                             # 用户选择
    is_riichi=True,                            # 用户选择
    dora_indicators=dora_result.actual_dora_tiles,  # 所有宝牌（含杠宝、里宝）
)

print(f"役种：{result.yaku_list}")
print(f"{result.han}番{result.fu}符 = {result.points}点")
```

**核心优化**：
✅ **移动手机调整角度**：用户通过移动手机调整拍摄角度，无需手动标记
✅ **和牌自动提取**：将和牌放最右边，系统自动识别，点击可修改
✅ **统一宝牌识别**：所有宝牌指示牌放一起拍，无需区分宝牌/杠宝/里宝
✅ **快速手动输入**：支持用户直接输入宝牌总数（<5秒）
✅ **所有结果可修改**：识别错误可直接点击修改，无需重新拍照

#### 优化建议

**拍照交互优化**
- 💡 将和牌放在最右边，手牌排成一排
- 📱 移动手机调整拍摄角度和距离，让所有牌清晰可见
- 🎯 自动检测最右边为和牌，无需手动标记
- ✏️ 用户可点击任意牌改为和牌（防止识别错误）
- 📊 实时显示识别结果预览和置信度

**宝牌输入优化**
- **优先级1**：拍宝牌区域（所有宝牌指示牌放一起）
- **优先级2**：手动输入总数（如"宝牌4个"）
- **优先级3**：下拉选择（常见数字0-5快速选择）
- 三种方式都支持，用户选最快的
- 系统统一识别，无需区分宝牌/杠宝/里宝


### 代码结构
```
AI-mahjong-calculator/
├── mahjong_calculator/  # 核心包
│   ├── __init__.py
│   ├── calculator/      # 计点引擎
│   │   ├── __init__.py
│   │   ├── tiles.py    # 牌的数据结构
│   │   ├── parser.py   # 手牌解析（面子、雀头）
│   │   ├── yaku.py     # 役种判断
│   │   ├── fu.py       # 符数计算
│   │   ├── points.py   # 点数计算
│   │   └── rules.py    # 规则配置
│   └── recognition/     # AI识别模块
│       ├── __init__.py
│       ├── model.py    # 模型加载
│       ├── preprocess.py # 图像预处理
│       ├── inference.py  # 推理逻辑
│       └── postprocess.py # 结果解析
├── models/              # 训练好的模型文件
│   └── mahjong_v1.onnx
├── training/            # 模型训练脚本
│   ├── train.py        # 训练主脚本
│   ├── data_augment.py # 数据增强
│   └── export_onnx.py  # 导出模型
├── data/                # 训练数据集（不上传git）
│   ├── raw/            # 原始照片
│   ├── labeled/        # 标注后的数据
│   └── splits/         # 训练/验证/测试集划分
├── tests/               # 测试用例
│   ├── test_tiles.py
│   ├── test_yaku.py
│   ├── test_calculator.py
│   ├── test_recognition.py
│   └── test_integration.py
├── examples/            # 使用示例
│   ├── example_calculate.py  # 计点示例
│   └── example_recognize.py  # 识别示例
├── docs/                # 文档
│   ├── API.md          # API 文档
│   └── YAKU_GUIDE.md   # 役种说明
├── setup.py             # 打包配置
├── requirements.txt     # 依赖列表
└── README.md            # 使用文档
```

### AI 模型设计

#### 麻将牌识别模型架构

**整体流程**
```
用户拍照 → 预处理 → 牌型检测 → 位置排序 → 和牌提取 → 置信度评分 → 返回结果
        OpenCV    YOLO/YOLOv8  坐标排序    最右边取值   多指标融合

说明：
- 用户将和牌放在最右边，其他手牌排成一排
- 系统通过检测x坐标最大的牌作为和牌
- 无需分割线或手动标记，用户移动手机调整角度
```

**推荐模型方案**

| 指标 | YOLOv8 Nano | MobileNetV3 | EfficientDet |
|------|-----------|-----------|------------|
| 推理速度 | 50-80ms | 60-100ms | 100-150ms |
| 模型大小 | 3.2MB | 2.5MB | 7-15MB |
| mac准确率 | >92% | >91% | >94% |
| 部署难度 | 简单 | 简单 | 中等 |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

**选择理由**：YOLOv8 Nano 是最佳平衡
- ✅ 足够快（<100ms），满足实时需求
- ✅ 足够准（>92%），日常使用无问题
- ✅ 足够小（3.2MB），易于集成到手机应用
- ✅ 生态成熟，文档完整

#### 训练数据收集计划

**采集目标**
| 参数 | 值 | 说明 |
|-----|-----|------|
| **每种牌** | 150-200张 | 足够学习光线/角度变化 |
| **总样本** | 5,100-6,800张 | 34种×150-200 |
| **采集周期** | 2-3周 | 日常拍摄收集 |
| **标注时间** | 3-4周 | 使用YOLO标注工具 |

**采集要求**
```
拍摄多样性：
├── 光线条件
│   ├── 室内自然光（靠窗）
│   ├── LED灯光（日光/黄光）
│   ├── 昏暗环境（夜间）
│   └── 强光/逆光
├── 摄像角度
│   ├── 0°（正面）
│   ├── 30°/ 45° / 60°（斜拍）
│   └── 90°（侧身）
├── 摄像距离
│   ├── 15-20cm（近距）
│   ├── 30-50cm（中距）
│   └── 50-100cm（远距）
├── 背景
│   ├── 木制麻将台
│   ├── 竹制麻将台
│   ├── 平坦白纸
│   └── 纹理床单
└── 遮挡情况
    ├── 完全展示
    ├── 部分遮挡（10-20%）
    └── 堆叠状态
```

**数据标注规范**

使用 YOLO 格式（`.txt`）标注：
```
# 示例：hand.jpg.txt
0 0.5 0.5 0.1 0.1    # class=0(1m), center=50%, size=10%
1 0.6 0.5 0.1 0.1    # class=1(2m)
2 0.7 0.5 0.1 0.1    # class=2(3m)
```

**手牌布局标注**
```
# 标注说明：
- 每张牌都带有bbox坐标
- 和牌通常在最右边（x坐标最大）
- 无需单独标注分割线
- 系统自动根据位置判断和牌
```

**数据集划分**
```
总样本 6,000 张
├── 训练集 70% (4,200张) → 模型学习
├── 验证集 15% (900张)   → 超参数调整
└── 测试集 15% (900张)   → 最终评估
```

#### 和牌位置检测算法

**需求背景**：用户将和牌放在最右边，系统自动识别

**实现方案**
```python
class WinTileDetector:
    """检测手牌中的和牌位置（最右边的牌）"""
    
    def detect_win_tile(self, detected_tiles) -> dict:
        """
        找到最右边的牌作为和牌
        
        算法步骤：
        1. YOLO识别所有14张牌，返回bbox坐标
        2. 根据bbox的x坐标排序（从左到右）
        3. 最右边的牌（x坐标最大）即为和牌
        4. 其余13张为手牌
        5. 计算置信度（检查是否有明显间隙）
        
        Params:
            detected_tiles: YOLO输出的所有牌（带bbox）
            
        Returns:
            {
                'hand_tiles': List[str],        # 手牌13张（按x坐标排序）
                'win_tile': str,                 # 和牌（最右边）
                'confidence': float,             # 检测置信度 0-1
                'method': str,                   # 'rightmost_position'
                'suggestion': str                # 提示用户确认
            }
        """
        # 按x坐标排序
        sorted_tiles = sorted(detected_tiles, key=lambda t: t['bbox'][0])
        
        # 最右边为和牌
        win_tile = sorted_tiles[-1]
        hand_tiles = sorted_tiles[:-1]
        
        # 计算置信度（检查是否有明显间隙）
        gap = win_tile['bbox'][0] - hand_tiles[-1]['bbox'][0]
        avg_gap = self._calc_avg_gap(hand_tiles)
        confidence = min(1.0, gap / (avg_gap * 1.5)) if avg_gap > 0 else 0.8
        
        return {
            'hand_tiles': [t['tile'] for t in hand_tiles],
            'win_tile': win_tile['tile'],
            'confidence': confidence,
            'method': 'rightmost_position'
        }
    
    def _calc_avg_gap(self, tiles) -> float:
        """计算牌之间的平均间隙"""
        if len(tiles) < 2:
            return 0
        gaps = [tiles[i+1]['bbox'][0] - tiles[i]['bbox'][0] 
                for i in range(len(tiles)-1)]
        return sum(gaps) / len(gaps)
```

**使用流程**
```
第2a步：用户拍手牌照片（将和牌放最右边）
  ↓
系统识别所有14张牌
  ↓
按x坐标排序，最右边为和牌
  ↓
显示预览给用户确认
  ├─ 确认正确 → 进入下一步
  └─ 需要修改 → 用户点击任意牌改为和牌
```

#### 置信度评分系统

**多维度评分**
```python
confidence_score = {
    'tile_detection': 0.95,        # 单张牌检测置信度（YOLO输出）
    'tile_classification': 0.92,   # 牌型分类准确度
    'win_tile_position': 0.99,     # 和牌位置准确度（x坐标最大）
    'overall': 0.96                # 综合置信度
}

# 判断是否需要用户确认
if confidence['overall'] < 0.85:
    show_warning("低置信度检测，请确认")
    allow_manual_correction = True
```

**置信度低的触发条件**
- 任意牌识别置信度 < 85%
- 检测到的牌数异常（不是13或14张）
- 照片质量差（模糊、暗、角度极端）
- 和牌与手牌的间隙不明显（需要用户确认）

#### 宝牌识别

**方案A：图像模板匹配（推荐）**
```python
import cv2

class DoraRecognizer:
    def __init__(self):
        # 预加载34种牌的清晰标准图作为模板
        self.templates = {
            '1m': load_template('tiles/1m.png'),
            '2m': load_template('tiles/2m.png'),
            # ... 其他33种牌
        }
    
    def recognize_dora(self, dora_image_path):
        """
        通过模板匹配识别宝牌指示牌
        
        优势：
        - 速度快（<50ms）
        - 准确率高（>98%）
        - 无需训练数据
        - 实现简单
        
        说明：
        - 用户将所有宝牌指示牌（宝牌、杠宝、里宝）放在一起拍照
        - 系统统一识别，不区分类型
        - 返回所有检测到的指示牌
        """
        img = cv2.imread(dora_image_path)
        best_matches = []
        
        for tile_name, template in self.templates.items():
            result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF)
            max_val = cv2.minMaxLoc(result)[1]
            best_matches.append((tile_name, max_val))
        
        # 返回所有检测到的宝牌指示牌（自动排序）
        dora_indicators = sorted(best_matches, key=lambda x: x[1], reverse=True)[:10]
        dora_indicators = [t for t in dora_indicators if t[1] > threshold]
        
        return {
            'indicators': [t[0] for t in dora_indicators],  # 所有指示牌
            'actual_dora': self.convert_to_actual(dora_indicators),  # +1转换
            'total_count': len(dora_indicators),
            'method': 'template_matching'
        }
```

**方案B：单独训练 YOLO 模型**
- 优势：可识别立直时的里宝
- 劣势：需要额外标注数据，推理时间稍长
- 建议：Dora 数据量不足时先用方案A，后续再升级

#### 模型训练配置

**硬件需求**
- GPU: NVIDIA RTX 2060 或以上（8GB显存）
- 无GPU可用 CPU 训练（需要1-2周）
- 推荐环境：Google Colab免费GPU

**训练超参数**
```python
# YOLOv8 Nano 训练配置
training_config = {
    'model': 'yolov8n.pt',              # 预训练模型
    'data': 'data/mahjong.yaml',        # 数据集配置
    'epochs': 100,                       # 训练轮数
    'imgsz': 640,                        # 输入图片大小
    'batch': 32,                         # 批次大小（64GB显存可用56）
    'device': 0,                         # GPU设备号
    'optimizer': 'SGD',                  # 优化器
    'lr0': 0.01,                         # 初始学习率
    'patience': 20,                      # 早停耐心值
    'augment': True,                     # 数据增强
}

# 预期结果
# - 训练时间：5-8小时（RTX2060）
# - mAP50: >92%
# - 推理时间：50-80ms/image
```

**导出为移动端格式**
```python
# 导出为 ONNX（Phase 1）
model.export(format='onnx')
# → models/mahjong_v1.onnx (3.2MB)

# 导出为 TFLite（Phase 2 Android）
model.export(format='tflite')
# → models/mahjong_v1.tflite (2.8MB)

# 导出为 CoreML（Phase 2 iOS）
model.export(format='coreml')
# → models/mahjong_v1.mlmodel (3.5MB)
```

### 任务清单

#### 模块 1：计点引擎

**1.1 基础数据结构**
- [ ] 定义牌的数据结构（万、筒、索、字牌）
- [ ] 枚举定义（牌类型、役种、场风等）
- [ ] 手牌表示类（含副露、立直等状态）

**1.2 手牌解析**
- [ ] 实现手牌标准型解析（4面子+1雀头）
- [ ] 七对子型解析
- [ ] 国士无双型解析（可选）
- [ ] 算法优化（快速判断听牌、已和）

**1.3 役种实现（按难度排序）**

**🟢 简单（4个）**
- [ ] 立直 (Riichi)
- [ ] 断幺九 (Tanyao)
- [ ] 役牌 (Yakuhai)
- [ ] 平和 (Pinfu)

**🟡 中等（8个）**
- [ ] 一杯口 (Iipeikou)
- [ ] 三色同顺 (Sanshoku Doujun)
- [ ] 一气通貫 (Ittsu)
- [ ] 混全带幺九 (Chanta)
- [ ] 七对子 (Chiitoitsu)
- [ ] 对对和 (Toitoi)
- [ ] 三暗刻 (Sanankou)
- [ ] 三色同刻 (Sanshoku Doukou)

**🔴 困难（6个）**
- [ ] 混一色 (Honitsu)
- [ ] 清一色 (Chinitsu)
- [ ] 二杯口 (Ryanpeikou)
- [ ] 纯全带幺九 (Junchan)
- [ ] 小三元 (Shousangen)
- [ ] 混老头 (Honroutou)

**役满（可选，后期实现）**
- [ ] 国士无双 (Kokushi Musou)
- [ ] 四暗刻 (Suuankou)
- [ ] 大三元 (Daisangen)
- [ ] 清老头 (Chinroutou)
- [ ] 字一色 (Tsuuiisou)

**1.4 计分系统**
- [ ] 符数计算（基础符、面子符、雀头符、边搭符等）
- [ ] 番数统计（累加所有役种）
- [ ] 点数表（根据番符计算点数）
- [ ] 场况处理（东家/非东家、自摸/荣和）

**1.5 API 接口设计**
```python
# 示例 API - 完整参数版本
from mahjong_calculator import Calculator

# 初始化
calc = Calculator()

# 计算点数（完整参数）
result = calc.calculate(
    # 必需参数
    hand="123m456p789s1122z",     # 手牌（13张，不含和牌）
    win_tile="2z",                 # 和牌
    
    # 和牌方式
    is_tsumo=False,                # 是否自摸（默认False=荣和）
    
    # 立直相关
    is_riichi=False,               # 是否立直
    is_double_riichi=False,        # 是否双立直（W立直）
    is_ippatsu=False,              # 是否一发
    
    # 座位信息
    is_dealer=False,               # 是否庄家（东家）
    prevalent_wind="E",            # 场风（E/S/W/N，默认E东场）
    seat_wind="S",                 # 自风（E/S/W/N，默认S南家）
    
    # 宝牌
    dora_indicators=["1z"],        # 宝牌指示牌（可多张）
    ura_dora_indicators=[],        # 里宝指示牌（立直时才有）
    
    # 其他特殊情况
    is_haitei=False,               # 是否海底捞月
    is_houtei=False,               # 是否河底捞鱼
    is_rinshan=False,              # 是否岭上开花
    is_chankan=False,              # 是否抢杠
    is_tenhou=False,               # 是否天和（庄家第一巡）
    is_chiihou=False,              # 是否地和（闲家第一巡）
    
    # 副露信息（如果有）
    melds=[],                      # 副露列表，格式如 [{"type": "pon", "tiles": "111m"}]
    
    # 本场相关
    honba=0,                       # 本场数（影响点数计算）
)

# 返回结果
print(result.yaku_list)   # [("断幺九", 1), ("役牌", 1)]
print(result.han)         # 2
print(result.fu)          # 30
print(result.base_points) # 2000（基础点）
print(result.points)      # 实际点数（含本场）
print(result.payment)     # 支付明细（谁付多少）

# 简化调用示例（使用默认值）
result = calc.calculate(
    hand="123m456p789s1122z",
    win_tile="2z",
    is_tsumo=True,
    dora_indicators=["1z"]
)
```

**1.6 测试覆盖**
- [ ] 每个役种至少2个测试用例（含边界情况）
- [ ] 符数计算测试（各种面子组合）
- [ ] 点数计算测试（不同番符对照表）
- [ ] 集成测试（完整和牌场景）

#### 模块 2：AI 识别模块

**2.1 数据准备**
- [ ] 拍摄/收集麻将牌照片（每种牌100+张）
- [ ] 标注工具选择（Labelme / LabelImg / CVAT）
- [ ] 数据标注（牌的位置和类型）
- [ ] 数据增强（旋转、光照、模糊、噪声）
- [ ] 数据集划分（训练集:验证集:测试集 = 8:1:1）

**2.2 模型训练**
- [ ] 选择模型架构（推荐：YOLOv8 / MobileNetV3）
- [ ] 编写训练脚本
- [ ] 超参数调优（学习率、批次大小等）
- [ ] 精度评估（目标：>95% 准确率）
- [ ] 训练过程监控（TensorBoard / WandB）

**2.3 模型部署**
- [ ] 转换模型为 ONNX 格式
- [ ] ONNX Runtime 推理引擎集成
- [ ] 推理速度优化（目标：单张图片 <1秒）
- [ ] CPU 推理测试
- [ ] 模型量化（减小模型体积）

**2.4 识别准确性优化**
- [ ] 处理不同光照条件（强光、弱光、侧光）
- [ ] 处理不同角度拍摄（俯拍、斜拍）
- [ ] 多张牌同时识别（手牌14张）
- [ ] 后处理优化（去重、排序、纠错）

**2.5 API 接口设计**
```python
# 示例 API
from mahjong_calculator import Recognizer

# 初始化
recognizer = Recognizer(model_path="models/mahjong_v1.onnx")

# 方法1：识别手牌（推荐用于识别玩家手牌）
hand_result = recognizer.recognize_hand(
    image_path="hand_photo.jpg",   # 图片路径
    # 或者传入 numpy 数组
    # image_array=np.array(...)
    sort=True,                      # 是否自动排序
    validate=True,                  # 是否验证牌数（应为13或14张）
)

# 返回结果
print(hand_result.tiles)         # ["1m", "2m", "3m", "4p", ...]（检测顺序）
print(hand_result.sorted_hand)   # "123m456p789s1122z"（排序后）
print(hand_result.confidence)    # [0.98, 0.95, 0.97, ...]（每张牌的置信度）
print(hand_result.tile_count)    # 14（检测到的牌数）
print(hand_result.bounding_boxes) # 每张牌的位置信息

# 方法2：识别宝牌指示牌（推荐用于识别宝牌区域）
dora_result = recognizer.recognize_dora(
    image_path="dora_photo.jpg",
    max_dora=5,                     # 最多识别几张宝牌（含杠后宝牌）
)

# 返回结果
print(dora_result.indicators)    # ["1z", "2m"]（宝牌指示牌）
print(dora_result.dora_tiles)    # ["2z", "3m"]（实际宝牌，自动转换）
print(dora_result.confidence)    # [0.99, 0.97]

# 方法3：通用识别（识别任意数量的牌）
result = recognizer.recognize(
    image_path="photo.jpg",
    min_tiles=1,                    # 最少牌数
    max_tiles=None,                 # 最多牌数（None=不限制）
)

print(result.tiles)              # 识别到的所有牌

# 完整使用示例：识别并计算
from mahjong_calculator import Recognizer, Calculator

# 步骤1：识别手牌
recognizer = Recognizer(model_path="models/mahjong_v1.onnx")
hand_result = recognizer.recognize_hand("my_hand.jpg")

# 步骤2：识别宝牌
dora_result = recognizer.recognize_dora("dora_area.jpg")

# 步骤3：用户选择和牌（从手牌中选一张）
win_tile = hand_result.tiles[-1]  # 假设最后一张是和牌

# 步骤4：计算点数（结合用户输入）
calc = Calculator()
calc_result = calc.calculate(
    hand=hand_result.sorted_hand[:-2],  # 去掉和牌后的手牌
    win_tile=win_tile,
    is_tsumo=True,                       # 用户输入
    is_riichi=True,                      # 用户输入
    dora_indicators=dora_result.indicators,
)

print(f"役种：{calc_result.yaku_list}")
print(f"{calc_result.han}番{calc_result.fu}符 = {calc_result.points}点")
```

#### 模块 3：集成测试

**3.1 单元测试**
- [ ] 计点引擎各模块单元测试
- [ ] 识别模块各函数单元测试
- [ ] 边界情况测试

**3.2 集成测试**
- [ ] 识别→计算完整流程测试
- [ ] 多组真实牌型测试（至少50组）
- [ ] 性能测试（识别速度、内存占用）
- [ ] 压力测试（批量处理）

**3.3 API 文档**
- [ ] 编写详细的 API 使用文档
- [ ] 提供多个使用示例（examples/ 目录）
- [ ] 常见问题和排错指南

#### 模块 4：打包发布

**4.1 Python 包打包**
- [ ] 编写 setup.py
- [ ] 打包为 wheel 格式
- [ ] 发布到 PyPI（可选）
- [ ] 编写安装和使用说明

**4.2 文档完善**
- [ ] README.md（快速开始）
- [ ] API 文档（详细使用说明）
- [ ] 贡献指南（如何参与开发）
- [ ] 示例代码（examples/ 目录）
- [ ] 役种说明文档（便于理解和测试）

---

## 第二期：iOS/安卓移动应用

**目标**：开发原生移动应用，集成第一期算法，添加语音播报功能。

### 技术选型

#### 方案 A：原生开发（推荐）
- **iOS**：Swift + SwiftUI，调用原生相机和 TTS
- **Android**：Kotlin + Jetpack Compose，原生性能最优
- **优势**：性能最佳、功能完整、用户体验好
- **挑战**：需要分别开发两个平台

#### 方案 B：跨平台开发
- **React Native**：一套代码，同时支持 iOS 和 Android
- **Flutter**：Dart 语言，性能接近原生
- **优势**：开发成本低、维护简单
- **挑战**：性能略逊于原生、某些功能需要原生桥接

### 代码结构

#### iOS 项目结构
```
MahjongCalculator-iOS/
├── MahjongCalculator/
│   ├── Models/          # 数据模型
│   ├── Views/           # UI 视图
│   │   ├── CameraView.swift      # 相机界面
│   │   ├── ResultView.swift      # 结果展示
│   │   └── HistoryView.swift     # 历史记录
│   ├── ViewModels/      # 视图模型
│   ├── Services/        # 服务层
│   │   ├── RecognitionService.swift  # 识别服务
│   │   ├── CalculatorService.swift   # 计算服务
│   │   └── TTSService.swift          # 语音播报
│   └── Resources/       # 资源文件
│       └── mahjong_v1.mlmodel        # Core ML 模型
└── MahjongCalculatorTests/
```

#### Android 项目结构
```
MahjongCalculator-Android/
├── app/
│   ├── src/main/
│   │   ├── java/com/example/mahjong/
│   │   │   ├── ui/              # UI 层
│   │   │   │   ├── CameraActivity.kt
│   │   │   │   ├── ResultActivity.kt
│   │   │   │   └── HistoryActivity.kt
│   │   │   ├── viewmodel/       # ViewModel
│   │   │   ├── service/         # 服务层
│   │   │   │   ├── RecognitionService.kt
│   │   │   │   ├── CalculatorService.kt
│   │   │   │   └── TTSService.kt
│   │   │   └── ml/              # ML 模型
│   │   └── assets/
│   │       └── mahjong_v1.tflite    # TensorFlow Lite 模型
│   └── src/test/
└── build.gradle
```

### 任务清单

#### 模块 1：算法移植

**1.1 识别算法集成**
- [ ] 将 ONNX 模型转换为 Core ML（iOS）
- [ ] 将 ONNX 模型转换为 TensorFlow Lite（Android）
- [ ] 集成模型到 App（离线推理）
- [ ] 图像预处理适配移动端
- [ ] 推理性能优化

**1.2 计点算法集成**
- [ ] 方案 A：通过 JNI/Native 调用 Python 代码（不推荐）
- [ ] 方案 B：将 Python 代码重写为 Swift/Kotlin（推荐）
- [ ] 单元测试验证算法正确性

#### 模块 2：移动端界面

**2.1 iOS 开发**
- [ ] 项目初始化（Xcode）
- [ ] 相机调用（AVFoundation）
- [ ] 拍照和图片选择
- [ ] 图片识别结果展示（可手动修正）
- [ ] **游戏状态输入界面**
  - [ ] 和牌方式选择（自摸/荣和）
  - [ ] 立直状态选择（立直/双立直/一发）
  - [ ] 座位信息输入（场风/自风/是否庄家）
  - [ ] 本场数输入
  - [ ] 里宝拍照识别（立直时）
  - [ ] 其他特殊役（海底、岭上等）
- [ ] 结果展示界面（役种、番符、点数）
- [ ] 历史记录管理
- [ ] 设置页面（默认值配置）

**2.2 Android 开发**
- [ ] 项目初始化（Android Studio）
- [ ] 相机调用（CameraX）
- [ ] 拍照和图片选择
- [ ] 图片识别结果展示（可手动修正）
- [ ] **游戏状态输入界面**（同 iOS）
- [ ] 结果展示界面
- [ ] 历史记录管理
- [ ] 设置页面

#### 模块 3：语音播报功能

**3.1 TTS 集成**
- [ ] iOS：集成 AVSpeechSynthesizer
- [ ] Android：集成 TextToSpeech
- [ ] 设计播报文案模板
- [ ] 支持中文和日文播报

**3.2 播报内容设计**
```
示例播报：
"识别完成。您的牌型是：断幺九，一杯口。共计3番30符，荣和2900点。"
"役满！您达成了国士无双，32000点！"
```

**3.3 用户体验优化**
- [ ] 播报速度可调
- [ ] 静音模式开关
- [ ] 支持中日双语切换
- [ ] 自定义播报内容

#### 模块 4：测试与优化

**4.1 功能测试**
- [ ] 识别准确率测试（实际场景）
- [ ] 计算正确性测试
- [ ] 语音播报测试
- [ ] 多设备兼容性测试

**4.2 性能优化**
- [ ] 识别速度优化（<2秒）
- [ ] 内存占用优化
- [ ] 电池消耗优化
- [ ] 界面流畅度优化

#### 模块 5：发布上线

**5.1 App Store（iOS）**
- [ ] 开发者账号申请（$99/年）
- [ ] 应用截图和描述准备
- [ ] 隐私政策编写
- [ ] TestFlight 内测
- [ ] 提交审核并上架

**5.2 Google Play（Android）**
- [ ] 开发者账号申请（$25一次性）
- [ ] 应用截图和描述准备
- [ ] APK 打包和签名
- [ ] 提交审核并上架

**5.3 推广运营**
- [ ] 使用文档和教程视频
- [ ] 社区推广（贴吧、知乎、B站）
- [ ] 收集用户反馈
- [ ] 持续迭代优化

---

## 第三期：微信小程序

**目标**：开发微信小程序版本，云端部署服务，降低用户使用门槛。

### 架构设计

```
小程序前端 ─┬─> 后端服务器 ─┬─> 识别服务（第一期算法）
            │               └─> 计点服务（第一期算法）
            │
            └─> 微信 API ──────> 语音播报（TTS）
```

### 代码结构

```
MahjongCalculator-Miniprogram/
├── miniprogram/         # 小程序前端
│   ├── pages/
│   │   ├── index/       # 首页（拍照/选图）
│   │   ├── result/      # 结果展示
│   │   └── history/     # 历史记录
│   ├── components/      # 组件
│   ├── utils/           # 工具函数
│   └── app.json         # 配置文件
├── cloudfunctions/      # 云函数（可选）
│   ├── recognize/       # 识别函数
│   └── calculate/       # 计算函数
└── backend/             # 后端服务（推荐）
    ├── app.py           # Flask/FastAPI 主程序
    ├── api/
    │   ├── recognize.py # 识别接口
    │   └── calculate.py # 计算接口
    ├── requirements.txt
    └── deploy/          # 部署配置
        ├── docker-compose.yml
        └── nginx.conf
```

### 任务清单

#### 模块 1：小程序前端

**1.1 页面开发**
- [ ] 小程序项目初始化
- [ ] 首页（拍照/相册选择）
- [ ] 识别结果确认页（展示识别结果，可手动修正）
- [ ] **游戏状态输入页**
  - [ ] 和牌方式选择
  - [ ] 立直状态选择
  - [ ] 座位信息输入
  - [ ] 本场数输入
  - [ ] 里宝识别（可选）
- [ ] 结果展示页（役种、番数、点数）
- [ ] 历史记录页
- [ ] 设置页（默认值、语音开关、语言选择）

**1.2 功能实现**
- [ ] 调用相机拍照（wx.chooseMedia）
- [ ] 图片上传到服务器
- [ ] 识别结果展示和手动修正
- [ ] 游戏状态选择组件开发
- [ ] 调用后端接口计算点数
- [ ] 结果展示和保存
- [ ] 语音播报（wx.createInnerAudioContext 或 TTS API）

#### 模块 2：后端服务

**2.1 云函数开发（方案 A）**
- [ ] 识别云函数（调用模型推理）
- [ ] 计算云函数（调用计点算法）
- [ ] 云存储配置（保存用户历史）
- [ ] 云数据库（用户数据管理）

**2.2 独立后端开发（方案 B，推荐）**
- [ ] Flask/FastAPI 项目搭建
- [ ] 图片上传接口
- [ ] 识别接口（调用第一期代码）
- [ ] 计算接口（调用第一期代码）
- [ ] 部署到云服务器（阿里云/腾讯云）

**2.3 性能优化**
- [ ] 模型轻量化
- [ ] 接口响应速度优化（<3秒）
- [ ] CDN 加速（图片传输）
- [ ] 缓存策略（减少重复计算）
- [ ] 限流和防刷

#### 模块 3：语音播报

**3.1 TTS 集成**
- [ ] 方案 A：微信 TTS 插件（需审核）
- [ ] 方案 B：第三方 TTS（百度/讯飞）
- [ ] 预生成音频文件（常见牌型）
- [ ] 动态合成音频（复杂牌型）

**3.2 播报内容**
- [ ] 播报文案模板设计
- [ ] 中日双语支持
- [ ] 播报速度可调

#### 模块 4：测试与发布

**4.1 测试**
- [ ] 功能测试（识别、计算、播报）
- [ ] 兼容性测试（不同手机型号）
- [ ] 压力测试（并发用户）
- [ ] 用户体验测试

**4.2 发布上线**
- [ ] 小程序账号注册
- [ ] 资质材料准备
- [ ] 隐私政策和用户协议
- [ ] 提交审核
- [ ] 发布上线

**4.3 运营推广**
- [ ] 使用教程编写
- [ ] 推广素材制作
- [ ] 社区推广
- [ ] 用户反馈收集

---

## 环境搭建

### 第一期环境配置

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/AI-mahjong-calculator.git
cd AI-mahjong-calculator

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行测试
pytest tests/

# 5. 使用示例
python examples/example_calculate.py
python examples/example_recognize.py
```

### requirements.txt 内容
```txt
# 核心依赖
numpy>=1.21.0
pillow>=9.0.0

# AI识别
torch>=1.12.0
torchvision>=0.13.0
opencv-python>=4.6.0
onnxruntime>=1.12.0

# 测试
pytest>=7.0.0
pytest-cov>=3.0.0

# 开发工具
black>=22.0.0
flake8>=4.0.0
mypy>=0.950
```

### 第二期环境配置

**iOS 开发环境**
- macOS 系统
- Xcode 14+
- CocoaPods（依赖管理）

**Android 开发环境**
- Android Studio
- Java JDK 11+
- Android SDK

**跨平台开发环境**
```bash
# React Native
npm install -g react-native-cli
npx react-native init MahjongCalculator

# Flutter
flutter doctor
flutter create mahjong_calculator
```

### 第三期环境配置

**微信小程序开发**
- 微信开发者工具
- Node.js 14+（如需云函数）

**后端开发**
```bash
# Flask
pip install flask flask-cors

# FastAPI
pip install fastapi uvicorn python-multipart
```

---

## 代码规范

### 命名风格
```python
# 文件名：小写下划线
mahjong_calculator/tiles.py

# 函数：小写下划线
def check_tanyao(hand):
    pass

# 类：驼峰命名
class TileParser:
    pass

# 常量：大写下划线
MAX_TILES = 14
```

### 注释要求
```python
def calculate_fu(hand, win_tile, is_tsumo):
    """
    计算符数
    
    Args:
        hand: 手牌列表
        win_tile: 和牌
        is_tsumo: 是否自摸
    
    Returns:
        int: 符数
    """
    pass
```

### 测试规范
```python
# 文件名：test_*.py
# tests/test_yaku.py

def test_tanyao_valid():
    """测试有效的断幺九"""
    hand = parse_hand("234m456p678s22z")
    assert check_tanyao(hand) == True

def test_tanyao_invalid():
    """测试无效的断幺九（含幺九牌）"""
    hand = parse_hand("123m456p789s22z")
    assert check_tanyao(hand) == False
```

---

## 如何贡献

### 新手友好任务
1. **实现简单役种** - 从 🟢 标记的役种开始
2. **编写测试用例** - 为已有功能补充测试
3. **改进文档** - 修正错别字、添加示例

### 提交流程
```bash
# 1. Fork 项目
# 2. 创建分支
git checkout -b feature/add-tanyao

# 3. 开发和测试
pytest tests/

# 4. 提交代码
git commit -m "feat: 实现断幺九役种判断"

# 5. 推送到你的仓库
git push origin feature/add-tanyao

# 6. 创建 Pull Request
```

---

## 参考资料

### 日麻规则
- [日本麻将维基](https://ja.wikipedia.org/wiki/麻雀の役一覧)
- [天凤规则](https://tenhou.net/man/)
- [雀魂规则](https://www.mjsoul.com/)

### 技术文档
- [PyTorch 官方教程](https://pytorch.org/tutorials/)
- [ONNX Runtime 文档](https://onnxruntime.ai/docs/)
- [Core ML 文档](https://developer.apple.com/documentation/coreml)
- [TensorFlow Lite 文档](https://www.tensorflow.org/lite)

---

## 常见问题

**Q: 完全不懂AI，能参与第一期吗？**  
A: 可以！计点引擎部分是纯算法，不需要AI知识。AI识别部分可以使用预训练模型或参考教程学习。

**Q: 数据集怎么获取？**  
A: 用手机拍摄自己的麻将牌即可，每种牌100+张，注意不同光照和角度。也可以寻找开源数据集。

**Q: 第一期要多久完成？**  
A: 预计2-4个月，取决于开发时间投入。计点引擎1个月，AI识别1-2个月，测试和打包1个月。

**Q: 为什么第一期不做GUI？**  
A: 专注算法实现，降低复杂度。GUI在第二期和第三期通过移动应用和小程序实现，用户体验更好。

**Q: 如何识别立直、自摸、本场等游戏状态？**  
A: **混合模式设计**：
- ✅ **通过拍照识别**：手牌（14张）、宝牌指示牌
- ❌ **用户手动输入**：自摸/荣和、立直、一发、本场数、场风/自风等
- 原因：这些游戏状态信息无法通过单张照片可靠识别，需要用户在界面上选择输入
- 第二期和第三期会提供友好的UI界面，通过下拉选择、单选框、多选框等方式快速输入

**Q: 拍照识别准确率能达到多少？**  
A: 目标 >95%。影响因素包括：光照条件、拍摄角度、麻将牌的清晰度。建议在良好光照下正面拍摄，App会提示用户调整。

**Q: 第二期必须同时开发iOS和Android吗？**  
A: 不必须。可以先开发一个平台，或者使用跨平台框架（React Native/Flutter）同时开发。

**Q: 微信小程序需要服务器吗？**  
A: 需要。可以用微信云开发（免费额度够用）或者自己购买云服务器。

**Q: 语音播报支持哪些语言？**  
A: 第二期和第三期优先支持中文，后续可扩展日语（原汁原味日麻体验）。

**Q: 能否支持其他麻将规则（如国标、广东麻将）？**  
A: 第一期专注日麻，算法架构设计时考虑可扩展性，后续可以添加其他规则。

---


**优先级排序**：
1. 计点引擎基础实现（tiles.py, parser.py）
2. 简单役种实现（断幺九、役牌、平和、立直）
3. 数据收集和标注（开始拍摄麻将牌照片）
4. 计分系统实现（符数、番数、点数）
5. AI模型选型和训练准备
