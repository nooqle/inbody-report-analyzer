# InBody Report Analyzer — Code Wiki

本文档面向代码阅读者，梳理该仓库的整体架构、模块职责、关键函数、依赖关系与运行方式，便于集成到任意 LLM 调用链路中。

## 1. 项目定位

该仓库提供一个极简的 Python “Skill/Prompt 生成器”，把 InBody 体测报告的 JSON 数据映射为：

- 系统提示词（System Prompt）：定义角色、分析框架、写作风格与输出结构
- 用户提示词（User Prompt）：把用户体测指标以固定格式填入模板

随后由调用方自行对接任意大模型（或注入 `llm_client`）生成最终的中文解读报告。

核心实现集中在 [agent.py](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py)。

## 2. 仓库结构

| 路径 | 类型 | 作用 |
|---|---|---|
| [agent.py](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py) | 核心代码 | 解析 InBody 数据、生成提示词、可选调用 LLM |
| [README.md](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/README.md) | 文档 | 功能概述、字段说明、集成示例 |
| [SKILL.md](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/SKILL.md) | 文档 | Skill 输入输出与设计理念（更偏产品/话术） |
| [system_prompt.md](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/system_prompt.md) | 文档 | 系统提示词长文档版（便于运营/编辑） |
| [sample_data.json](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/sample_data.json) | 样例 | 体测数据样例（作为 `agent.py` 的演示输入） |
| [sample_output.txt](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/sample_output.txt) | 样例 | 对应样例的解读输出示例 |
| [test_skill.py](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/test_skill.py) | 测试脚本 | 生成测试用 prompts，并写入固定路径文件 |
| [test_result.md](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/test_result.md) | 文档 | 一次测试评估记录（风格/模块/改进点） |

## 3. 架构与数据流

### 3.1 高层架构

该项目本质是“模板 + 字段映射 + 可选的 LLM 适配层”：

```
InBody JSON (raw)
  ↓
parse_inbody_data(): 字段清洗/兜底/归一化
  ↓
generate_user_prompt(): 套 USER_PROMPT_TEMPLATE
  ↓
analyze_inbody_report():
  ├─ 无 llm_client：返回 {system_prompt, user_prompt}
  └─ 有 llm_client：调用 llm_client.chat(...) 返回解读文本
```

### 3.2 运行边界与职责划分

- 本仓库负责：
  - 提取少量关键指标（年龄、性别、BMI、体脂、内脏脂肪、骨骼肌、相位角等）
  - 生成一套稳定的提示词输入（system/user）
- 本仓库不负责：
  - 调用任何具体大模型 SDK（仅提供 `llm_client` 的注入点）
  - 服务化部署（FastAPI/Flask 示例仅在文档中给出）
  - 指标区间的严谨医学判定（提示词中的阈值属于话术策略的一部分）

## 4. 核心模块：agent.py

### 4.1 常量：SYSTEM_PROMPT / USER_PROMPT_TEMPLATE

- `SYSTEM_PROMPT`：[agent.py:L11-L74](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L11-L74)
  - 定义角色、语气、8 段输出结构、关键指标解释逻辑与比喻风格
  - 内容在 [system_prompt.md](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/system_prompt.md) 中有一份更易维护的长文档版
- `USER_PROMPT_TEMPLATE`：[agent.py:L77-L110](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L77-L110)
  - 固定列出“用户基础信息 + 核心指标”，并强制输出模块标题顺序（八段）

### 4.2 关键函数：parse_inbody_data

函数位置：[parse_inbody_data](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L112-L162)

职责：

- 从输入 `data: Dict[str, Any]` 中读取关键字段
- 处理缺失值/空字符串/"null" 的兜底
- 把可能为字符串的数值字段转成 `int/float`
- 统一字段命名，输出一份“提示词可用”的规范化字典

内部工具函数：

- `safe_get(key, default)`：[agent.py:L165-L169](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L165-L169)
- `safe_float(key, default)`：[agent.py:L171-L178](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L171-L178)
- `safe_int(key, default)`：[agent.py:L180-L187](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L180-L187)

字段映射要点（节选）：

- 性别：
  - `sex` → `sex_text`（`1 => 男性`, 其它 => `女性`）：[agent.py:L189-L190](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L189-L190)
- 脂肪控制量：
  - 优先 `fatControl`，否则用 `bfmControl`：[agent.py:L201-L201](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L201-L201)
- 肌肉控制量：
  - 优先 `muscleControl`，否则用 `ffmControl`：[agent.py:L217-L217](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L217-L217)
- 内脏脂肪等级：
  - 优先 `vfl`，否则用 `vfaLevel`：[agent.py:L220-L220](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L220-L220)
- 水分比率：
  - 优先 `ecwOrTbw`，否则用 `lowerLimitEcwOrTbw`：[agent.py:L221-L221](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L221-L221)
- 基础代谢：
  - 优先 `bmr`，否则用 `basalMetabolicRate`：[agent.py:L222-L222](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L222-L222)
- 腰臀比：
  - 优先 `waistHipRatio`，否则用 `whr`：[agent.py:L223-L223](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L223-L223)

输入样例可参考 [sample_data.json](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/sample_data.json)。

### 4.3 关键函数：generate_user_prompt

函数位置：[generate_user_prompt](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L227-L251)

职责：

- 调用 `parse_inbody_data()` 获取规范化字段
- 将字段填充进 `USER_PROMPT_TEMPLATE.format(...)`，输出最终 user prompt 字符串

### 4.4 关键函数：build_prompts

函数位置：[build_prompts](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L254-L268)

职责：

- 生成 `{system_prompt, user_prompt}` 供 agent 统一调度大模型
- 根据 `output_format` 拼接输出约束：
  - `output_format="json"`：在系统提示词末尾追加 JSON Schema 约束（用于前端渲染）
  - `output_format="markdown"`：沿用原本“八段结构”的纯文本输出约束

### 4.5 关键函数：analyze_inbody_report

函数位置：[analyze_inbody_report](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L286-L320)

职责：

- 调用 `build_prompts(...)` 得到 prompts
- 若未注入 `llm_client`：返回 prompts（system/user/output_format）
- 若注入 `llm_client`：
  - `output_format="json"`：要求模型输出严格 JSON，并尝试解析为 Python dict 返回
  - `output_format="markdown"`：直接返回模型生成的 Markdown 文本

对 `llm_client` 的隐式约定：

- 需要提供一个 `chat(...)` 方法
- 入参名为 `system_prompt` 与 `user_prompt`
- 返回值是最终的中文解读文本（字符串）

### 4.6 脚本入口：__main__

入口位置：[agent.py:L323-L340](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L323-L340)

- 读取本地 `sample_data.json`
- 调用 `analyze_inbody_report(sample["data"])`
- 打印系统提示词前 500 字，以及完整用户提示词

该入口用于快速验证 prompts 是否生成正确，不会实际调用大模型。

## 5. 辅助脚本：test_skill.py

文件：[test_skill.py](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/test_skill.py)

用途：

- 内置一份“样例 1”的测试数据 `sample_data`：[test_skill.py:L11-L37](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/test_skill.py#L11-L37)
- 定义了一个简化版 `generate_user_prompt(data)`（与 `agent.py` 的实现并行存在）：[test_skill.py:L106-L142](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/test_skill.py#L106-L142)
- 把 prompts 写入固定路径：`/workspace/projects/inbody-report-analyzer/test_prompts.txt`：[test_skill.py:L164-L176](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/test_skill.py#L164-L176)

注意点（阅读/集成时需要知道）：

- `test_skill.py` 中 `import requests` 当前未使用：[test_skill.py:L6-L8](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/test_skill.py#L6-L8)
- 文件写入路径是硬编码的 `/workspace/...`，在非容器/非特定环境下可能不存在导致报错
- `test_skill.py` 内含一份 `SYSTEM_PROMPT` 文本，与 [agent.py](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py) 的提示词存在重复维护

## 6. 依赖关系

### 6.1 Python 依赖

- 核心运行（生成 prompts）仅依赖 Python 标准库：
  - `json`, `typing`：[agent.py:L7-L8](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/agent.py#L7-L8)
- 测试脚本额外 `import requests`，但当前未使用：[test_skill.py:L6-L8](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/test_skill.py#L6-L8)

仓库未提供 `requirements.txt` / `pyproject.toml`，环境管理由使用方自行决定。

### 6.2 外部系统依赖（集成层）

为了生成最终解读文本，需要外部提供大模型调用能力，常见方式：

- 在业务代码中自行调用任意 LLM SDK（OpenAI / Azure / 其他厂商）
- 注入实现了 `chat(system_prompt, user_prompt)` 的 `llm_client` 给 `analyze_inbody_report`

## 7. 输出内容与“五段结构”

提示词约束的报告结构为五个大模块（固定顺序）：

1. 分数解读
2. 负向指标分析
3. 正向资本盘点
4. 四维耦合改善策略（内含：睡眠、情绪、运动、饮食）
5. 课程推荐

示例输出可参考 [sample_output.txt](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/sample_output.txt) 与测试评估 [test_result.md](file:///Users/qiaole/Downloads/projects/inbody-report-analyzer/test_result.md)。

## 8. 运行与集成方式

### 8.1 本地快速验证（仅生成 prompts）

在仓库根目录运行：

```bash
python agent.py
```

结果：

- 终端打印系统提示词的前 500 字（用于快速确认内容）
- 终端打印完整用户提示词（包含已填充的关键指标）

### 8.2 作为库集成（推荐）

业务侧直接 import 核心函数，生成 prompts 并调用你的 LLM 客户端：

```python
import json
from agent import SYSTEM_PROMPT, generate_user_prompt

with open("sample_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)["data"]

user_prompt = generate_user_prompt(data)
response = your_llm_client.chat(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
print(response)
```

### 8.3 注入 llm_client（把 LLM 调用放进函数）

`analyze_inbody_report` 支持直接注入 `llm_client`：

```python
import json
from agent import analyze_inbody_report

with open("sample_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)["data"]

report_text = analyze_inbody_report(data, llm_client=your_llm_client)
print(report_text)
```

## 9. 可维护性与扩展建议（面向二次开发）

该仓库当前的设计非常轻量，适合快速嵌入多种系统；但在规模化使用前，通常会做以下整理：

- 单一来源：让 `SYSTEM_PROMPT` 只维护在一个地方（例如从 `system_prompt.md` 读取，或反过来由代码生成文档）
- 字段覆盖：将更多 InBody 字段（正常范围、标准值、变化趋势、CIDP 等）纳入 `parse_inbody_data`，并在 user prompt 中表达
- 数据类型：明确 `measureEpochMilli` 的真实类型（当前样例是日期字符串，并非 epoch 毫秒值），避免下游误判
- 适配层：为 `llm_client` 定义一个清晰的 Protocol/接口契约，便于多厂商 SDK 统一接入
