# InBody 体测报告智能解读 Skill

## 概述
本 Skill 用于将 InBody 体测报告的 JSON 数据转化为人性化、接地气的智能解读报告。输出内容包含分数解读、负向指标分析、正向资本盘点、四维改善策略（饮食、运动、睡眠、情绪）及课程引流。

## 输入格式
JSON 格式的 InBody 体测报告数据，包含以下核心字段：

### 基础信息
- `age`: 年龄
- `sex`: 性别（1: 男性, 2: 女性）
- `height`: 身高
- `weight`: 体重
- `measureEpochMilli`: 测量时间

### 核心评分
- `score`: InBody 得分（满分100，及格线通常70-80分）
- `scoreChange`: 上次得分变化

### 脂肪相关指标
- `bodyFatScale`: 体脂率（%）
- `bodyFatScaleLimitLower/Upper`: 体脂率正常范围
- `bfm`: 体脂肪量
- `bfmStandard`: 标准脂肪量
- `fatControl`/`bfmControl`: 脂肪控制量（负值表示需要减少）
- `vfaLevel`/`vfl`: 内脏脂肪等级（正常范围1-9，≥10需警惕，≥15高危）
- `visceralFat`: 内脏脂肪指数
- `whr`: 腰臀比（女性正常≤0.85，男性正常≤0.90）

### 肌肉相关指标
- `muscle`: 肌肉量
- `muscleStandard`: 标准肌肉量
- `muscleLimitLower/Upper`: 肌肉量正常范围
- `muscleControl`/`ffmControl`: 肌肉控制量（正值表示需要增加）
- `smm`: 骨骼肌量
- `smmStandard`: 标准骨骼肌量
- `smmLimitLower/Upper`: 骨骼肌正常范围
- `skeletonMuscle`: 骨骼肌

### 骨骼与矿物质
- `bmc`: 骨矿物质含量
- `bmcLimitLower/Upper`: 骨矿物质正常范围
- `mineral`: 矿物质（无机盐）
- `mineralLimitLower/Upper`: 矿物质正常范围

### 身体水分与细胞健康
- `tbw`: 总体水分
- `tbwLimitLower/Upper`: 总体水分正常范围
- `ecwOrTbw`: 细胞外水分比率（正常范围0.360-0.390，越低越好）
- `lowerLimitEcwOrTbw`/`upperLimitEcwOrTbw`: 细胞外水分比率正常范围
- `wholeBodyPhaseAngle50khz`: 全身相位角（越高越好，是细胞活力的重要指标）

### 代谢相关
- `bmr`/`basalMetabolicRate`: 基础代谢率
- `bmi`: 体质指数（正常范围18.5-24）
- `bodyAge`: 身体年龄

### 体型分析
- `cidp`: CIDP 分析类型
- `cidpType`: CIDP 类型编号
- `cidpDesc`: CIDP 描述
- `cidpDirection`: CIDP 方向说明

## 输出格式
人性化的体测报告解读，包含以下五个大模块：

### 一、分数解读（破冰定调）
- 将分数具象化，用"满载的汽车"等比喻
- 先肯定用户基础，再指出改善空间

### 二、负向指标分析（痛点挖掘）
- 脂肪超载：计算超标量，用"背大米"等生活化比喻
- 内脏脂肪：解释危害，用"厚羽绒服"等比喻
- 肌肉储备：说明对代谢和跌倒风险的影响

### 三、正向资本盘点（信心赋能）
- 细胞活力（相位角）：包装为"电池健康度"、"抗衰老资本"
- 骨骼健康：强调行动自由度
- 体内环境：水分比率好=没有慢性炎症

### 四、四维耦合改善策略
（基于国家级《健康生活方式指导原则》）
1. 睡眠改善（排在首位）
2. 情绪改善
3. 运动改善
4. 饮食改善（抗衰蛋白注重植物蛋白及代谢问题、抗炎营养素、卵磷脂与鱼油协同机制）

### 五、课程引流
- 引导学习《轻松"享瘦" 营养先行》课程
- 组队学/自己学选项
- 数据支撑：社群参与者的身心健康、快乐幸福指数比非参与者高出 1.5 倍，且与国务院发展研究中心合作的《社群体重管理研究白皮书》已正式发布

## 使用方法（面向 Agent 集成）

### 方式一：只生成 prompts（由 Agent 统一调用大模型）

```python
import json
from agent import build_prompts

with open("sample_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)["data"]

prompts = build_prompts(data, output_format="json")
system_prompt = prompts["system_prompt"]
user_prompt = prompts["user_prompt"]
```

### 方式二：直接返回结构化 JSON（推荐用于前端渲染）

```python
import json
from agent import analyze_inbody_report

with open("sample_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)["data"]

report_json = analyze_inbody_report(data, llm_client=your_llm_client, output_format="json")
```

### 方式三：直接返回 Markdown 文本（前端直接渲染 Markdown）

```python
import json
from agent import analyze_inbody_report

with open("sample_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)["data"]

report_md = analyze_inbody_report(data, llm_client=your_llm_client, output_format="markdown")
```
