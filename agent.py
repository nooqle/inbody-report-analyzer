"""
InBody 体测报告智能解读 Agent Skill
输入：InBody 体测报告 JSON 数据
输出：人性化解读报告
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# 系统提示词
SYSTEM_PROMPT = """你是一位专业的 InBody 体测报告解读助手，擅长将枯燥的体测数据翻译成通俗易懂、接地气、有人情味的健康建议。

你的解读风格：
1. 像朋友聊天，不说教
2. 用生活化比喻（背大米、厚羽绒服、发动机保养）
3. 先肯定用户的基础，建立信心
4. 数据说话，但用通俗方式解释
5. 给出具体可行的建议

## 分析框架

### 一、破冰定调与分数解读
读取 score 字段：
- 70-80分：及格线，身体基本正常
- 60-70分：需要"稍微搭把手"
- 60分以下：需重点关注

用"满载的汽车"等比喻，先肯定基础，再指出改善空间。

### 二、负向指标排雷
1. 脂肪超载：计算 fatControl/bfmControl（负值=需减少量）
   - 话术："每天背着近XX斤的大米生活"
   
2. 内脏脂肪：读取 vfaLevel/vfl（1-9正常，10-14警惕，≥15高危）
   - 话术："给肝脏穿了一件厚羽绒服"
   
3. 肌肉储备：读取 smm、muscleControl
   - 话术："发动机变小，热量难消耗"

### 三、正向资本盘点
1. 相位角（wholeBodyPhaseAngle50khz）：
   - 如果有数据（>0），高=细胞年轻。话术："电池健康度，抗老能力超强"
   - 如果缺失或为0，则从下面其他指标中重点挖掘闪光点。
   
2. 骨骼（bmc/minerals）：好=能承受运动
   - 话术："骨架结实，行动自由度极高"
   
3. 水分比率（ecwOrTbw）：低=无炎症
   - 话术："循环顺畅，减脂效果出奇快"

### 四、四维耦合改善策略
（基于国家级《健康生活方式指导原则》，必须结合用户前面的具体数据（如肌肉缺口、内脏脂肪等级）给出个性化建议，而非生硬背诵以下策略）
1. 睡眠（良好睡眠）
   - 每晚7-8小时高质量睡眠，睡前避免刷手机、喝咖啡
2. 情绪（积极心态）
   - 社交对身心健康的益处，数据：社群参与者的身心健康、快乐幸福指数比非参与者高出1.5倍
   - 推荐社群参与：舞蹈团，健步走，合唱团，八段锦队，马拉松跑团等
3. 运动（合理运动）
   - 结合用户骨骼肌（smm）或肌肉缺口（muscleControl）推荐力量训练：弹力带、小哑铃、扶椅深蹲
   - 结合用户脂肪超标（fatControl）推荐有氧运动：每周3-4次，30-40分钟，快步走/游泳/骑车
4. 饮食（均衡营养）
   - 针对肌肉缺口补充抗衰蛋白：鱼虾、鸡胸、豆腐、鸡蛋、乳清蛋白粉
   - 针对内脏脂肪（vfl）或炎症补充抗炎营养素：黄酮、多酚、花青素含量高的水果蔬菜
   - 血管清道夫：深海鱼油（Omega-3）清除脂肪，搭配卵磷脂将其运输出去，协同守护心血管
   - 针对腰臀比和内脏脂肪替换低GI主食：燕麦、糙米、红薯、玉米

### 五、课程引流
- 《轻松"享瘦" 营养先行-现代人体质量管理观念6课》
- 数据支撑：与国务院发展研究中心合作的《社群体重管理研究白皮书》已正式发布

## 输出格式
直接输出解读内容，使用中文，按五个大模块分段（一至三为数据解读，四为四维策略，五为课程推荐），每个模块有标题。
"""

JSON_OUTPUT_INSTRUCTIONS = """你必须严格按 JSON 输出，不要输出任何额外文本，不要使用 Markdown 代码块包裹。

输出 JSON Schema（必须包含这些字段）：
{
  "version": "1.0",
  "format": "inbody_report",
  "user": {
    "age": number,
    "sex": "男性" | "女性",
    "height_cm": number,
    "weight_kg": number,
    "measure_time": string
  },
  "metrics": {
    "score": number,
    "bmi": number,
    "pbf": number,
    "bfm_kg": number,
    "fat_control_kg": number,
    "fat_control_jin": number,
    "smm_kg": number,
    "muscle_control_kg": number,
    "bmc_kg": number,
    "phase_angle": number,
    "vfl": number,
    "ecw_tbw": number,
    "bmr_kcal": number,
    "whr": number
  },
  "report": {
    "score_interpretation": {"title": "一、分数解读", "content_md": string},
    "negative_indicators": {"title": "二、负向指标分析", "content_md": string},
    "positive_capital": {"title": "三、正向资本盘点", "content_md": string},
    "four_dimensions": {
      "title": "四、四维耦合改善策略",
      "content_md": string,
      "sleep": {"title": "1. 睡眠改善", "content_md": string},
      "mood": {"title": "2. 情绪改善", "content_md": string},
      "exercise": {"title": "3. 运动改善", "content_md": string},
      "diet": {"title": "4. 饮食改善", "content_md": string}
    },
    "course": {"title": "五、课程推荐", "content_md": string}
  },
  "highlights": {
    "risks": string[],
    "advantages": string[],
    "next_actions": string[]
  }
}

content_md 字段允许包含 Markdown（用于前端渲染），但整体外层必须是严格 JSON。"""

# 用户提示词模板
USER_PROMPT_TEMPLATE = """请解读以下 InBody 体测报告数据，输出人性化、接地气的解读报告。

## 用户基础信息
- 年龄：{age} 岁
- 性别：{sex_text}
- 身高：{height} cm
- 体重：{weight} kg
- 测量时间：{measure_time}

## 核心指标
- InBody 得分：{score} 分
- BMI：{bmi}
- 体脂率：{pbf}%
- 体脂肪量：{bfm} kg
- 脂肪控制：{fat_control} kg
- 脂肪控制（约合）：{fat_control_jin} 斤
- 骨骼肌：{smm} kg
- 肌肉控制：{muscle_control} kg
- 骨矿物质：{bmc} kg
- 相位角：{phase_angle}°
- 内脏脂肪等级：{vfl}
- 细胞外水分比率：{ecw_tbw}
- 基础代谢率：{bmr} kcal
- 腰臀比：{whr}

## 请按以下格式输出解读报告：
一、分数解读
二、负向指标分析
三、正向资本盘点
四、四维耦合改善策略
五、课程推荐
"""

def parse_inbody_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """解析 InBody 数据，提取关键字段"""
    
    def safe_get(key: str, default=None):
        value = data.get(key)
        if value is None or value == "" or value == "null":
            return default
        return value
    
    def safe_float(key: str, default=0.0):
        value = safe_get(key, default)
        if value is None:
            return default
        try:
            return float(value)
        except:
            return default
    
    def safe_int(key: str, default=0):
        value = safe_get(key, default)
        if value is None:
            return default
        try:
            return int(float(value))
        except:
            return default
    
    sex = safe_int("sex", 1)
    sex_text = "男性" if sex == 1 else "女性"

    measure_time = safe_get("measureEpochMilli", "未知")
    if isinstance(measure_time, (int, float)) or (isinstance(measure_time, str) and measure_time.strip().isdigit()):
        try:
            ms = int(float(measure_time))
            if ms > 10_000_000_000:
                measure_time = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            pass

    fat_control = safe_float("fatControl", 0) or safe_float("bfmControl", 0)
    
    return {
        "age": safe_int("age", 30),
        "sex": sex,
        "sex_text": sex_text,
        "height": safe_float("height", 170),
        "weight": safe_float("weight", 70),
        "measure_time": measure_time,
        "score": safe_int("score", 70),
        "bmi": safe_float("bmi", 22),
        "pbf": safe_float("pbf", 25),
        "bfm": safe_float("bfm", 20),
        "fat_control": fat_control,
        "fat_control_jin": round(abs(fat_control) * 2, 1),
        "smm": safe_float("smm", 30),
        "muscle_control": safe_float("muscleControl", 0) or safe_float("ffmControl", 0),
        "bmc": safe_float("bmc", 3),
        "phase_angle": safe_float("wholeBodyPhaseAngle50khz", 5),
        "vfl": safe_int("vfl", 5) or safe_int("vfaLevel", 5),
        "ecw_tbw": safe_float("ecwOrTbw", 0.38) or safe_float("lowerLimitEcwOrTbw", 0.38),
        "bmr": safe_int("bmr", 1500) or safe_int("basalMetabolicRate", 1500),
        "whr": safe_float("waistHipRatio", 0.85) or safe_float("whr", 0.85),
    }


def generate_user_prompt(data: Dict[str, Any]) -> str:
    """生成用户提示词"""
    parsed = parse_inbody_data(data)
    
    return USER_PROMPT_TEMPLATE.format(
        age=parsed["age"],
        sex_text=parsed["sex_text"],
        height=parsed["height"],
        weight=parsed["weight"],
        measure_time=parsed["measure_time"],
        score=parsed["score"],
        bmi=parsed["bmi"],
        pbf=parsed["pbf"],
        bfm=parsed["bfm"],
        fat_control=parsed["fat_control"],
        fat_control_jin=parsed["fat_control_jin"],
        smm=parsed["smm"],
        muscle_control=parsed["muscle_control"],
        bmc=parsed["bmc"],
        phase_angle=parsed["phase_angle"],
        vfl=parsed["vfl"],
        ecw_tbw=parsed["ecw_tbw"],
        bmr=parsed["bmr"],
        whr=parsed["whr"],
    )


def build_prompts(data: Dict[str, Any], output_format: str = "json") -> Dict[str, str]:
    parsed = parse_inbody_data(data)
    user_prompt = generate_user_prompt(data)

    if output_format == "json":
        system_prompt = SYSTEM_PROMPT + "\n\n" + JSON_OUTPUT_INSTRUCTIONS
    else:
        system_prompt = SYSTEM_PROMPT

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "output_format": output_format,
        "parsed": json.dumps(parsed, ensure_ascii=False),
    }


def _extract_json_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    s = text.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
            s = "\n".join(lines[1:-1]).strip()
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return s[start : end + 1]
    return s


def analyze_inbody_report(
    data: Dict[str, Any],
    llm_client=None,
    output_format: str = "json",
) -> Any:
    """
    分析 InBody 报告并生成解读
    
    Args:
        data: InBody 报告 JSON 数据
        llm_client: LLM 客户端（可选，用于实际调用大模型）
        output_format: "json" 或 "markdown"
    
    Returns:
        人性化解读报告文本
    """
    prompts = build_prompts(data, output_format=output_format)

    if not llm_client:
        return {
            "system_prompt": prompts["system_prompt"],
            "user_prompt": prompts["user_prompt"],
            "output_format": output_format,
        }

    response = llm_client.chat(
        system_prompt=prompts["system_prompt"],
        user_prompt=prompts["user_prompt"],
    )

    if output_format == "json":
        json_text = _extract_json_text(response)
        return json.loads(json_text)

    return response


# 示例使用
if __name__ == "__main__":
    # 加载示例数据
    with open("sample_data.json", "r", encoding="utf-8") as f:
        sample = json.load(f)
    
    # 生成提示词
    result = analyze_inbody_report(sample["data"])
    
    print("=" * 50)
    print("系统提示词:")
    print("=" * 50)
    print(result["system_prompt"][:500] + "...")
    
    print("\n" + "=" * 50)
    print("用户提示词:")
    print("=" * 50)
    print(result["user_prompt"])
