# InBody 体测报告智能解读 Skill

## 功能概述
将 InBody 体测报告的 JSON 数据转化为人性化、接地气的智能解读报告。

## 输入输出

### 输入
JSON 格式的 InBody 体测报告数据

### 输出
包含五个模块的人性化解读报告：
1. 分数解读（破冰定调）
2. 负向指标分析（痛点挖掘）
3. 正向资本盘点（信心赋能）
4. 四维耦合改善策略（睡眠、情绪、运动、饮食）
5. 课程推荐

## 使用方法

### 方式一：直接调用 LLM
```python
from agent import analyze_inbody_report, SYSTEM_PROMPT, generate_user_prompt

# 加载数据
import json
with open("sample_data.json") as f:
    data = json.load(f)["data"]

# 生成提示词
user_prompt = generate_user_prompt(data)

# 调用大模型
response = your_llm_client.chat(
    system_prompt=SYSTEM_PROMPT,
    user_prompt=user_prompt
)
print(response)
```

### 方式二：让 Skill 输出结构化 JSON（推荐用于 Agent → 前端渲染）
```python
import json
from agent import analyze_inbody_report

with open("sample_data.json") as f:
    data = json.load(f)["data"]

report_json = analyze_inbody_report(data, llm_client=your_llm_client, output_format="json")
print(report_json["highlights"]["next_actions"])
```

### 方式三：只生成 prompts（由 Agent 统一调用大模型）
```python
import json
from agent import build_prompts

with open("sample_data.json") as f:
    data = json.load(f)["data"]

prompts = build_prompts(data, output_format="json")
system_prompt = prompts["system_prompt"]
user_prompt = prompts["user_prompt"]
```

### 方式二：作为 API 服务
```python
# 在 FastAPI/Flask 中集成
@app.post("/api/inbody/analyze")
async def analyze_report(request: Request):
    data = await request.json()
    result = analyze_inbody_report(data, llm_client=your_llm, output_format="json")
    return {"report": result}
```

## 核心设计理念

### 1. 破冰定调
- 将抽象分数具象化（"满载的汽车"比喻）
- 先肯定基础，再指出改善空间

### 2. 痛点挖掘
- 不报冰冷数据，只说"后果"
- 生活化比喻：背大米、厚羽绒服、发动机

### 3. 信心赋能
- 挖掘高级指标（相位角、骨矿物质）
- 包装为"王牌资本"、"抗衰老资本"

### 4. 四维耦合改善策略
- 强调：睡眠、情绪、运动、饮食四个维度
- **核心限制**：睡眠、情绪、运动三个维度**必须且只能输出1条最核心**的精准建议。
- **饮食维度**：必须且仅包含“抗衰蛋白、抗炎营养素、血管清道夫、主食替换”四个方面的指导原则，每个方面出1条精简建议。
- 与国家级《健康生活方式指导原则》契合

### 5. 数据支撑
- 情绪：社群参与者的身心健康、快乐幸福指数比非参与者高出 1.5 倍
- 课程：与国务院发展研究中心合作的《社群体重管理研究白皮书》已正式发布。**严格限制只推荐《轻松"享瘦" 营养先行》课程**。

## 文件结构
```
inbody-report-analyzer/
├── README.md           # 本文件
├── SKILL.md            # Skill 定义文档
├── agent.py            # 核心分析逻辑
├── sample_data.json    # 示例数据
└── sample_output.txt   # 示例输出
```

## 核心字段映射

| JSON 字段 | 含义 | 用途 |
|-----------|------|------|
| score | InBody得分 | 分数解读 |
| fatControl/bfmControl | 脂肪控制量 | 脂肪超载分析 |
| vfl/vfaLevel | 内脏脂肪等级 | 内脏脂肪分析 |
| smm | 骨骼肌 | 肌肉储备分析 |
| wholeBodyPhaseAngle50khz | 相位角 | 细胞活力评估 |
| bmc | 骨矿物质 | 骨骼健康评估 |
| ecwOrTbw | 细胞外水分比率 | 体内炎症评估 |
