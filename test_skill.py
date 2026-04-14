"""
测试 InBody 体测报告智能解读 Skill
使用样例1数据：58岁女性，BMI 34.1，得分59分
"""

import json
import requests
import os

# 样例1数据（inbody570）
sample_data = {
    "targetWeight": 44.50,
    "weight": 70.00,
    "bmi": 34.1,
    "bfm": 32.90,
    "fatControl": -25.5,
    "muscleControl": 0.0,
    "measureEpochMilli": "2025-05-06 16:07:00",
    "height": 156.0,
    "age": 58,
    "sex": "2",
    "score": "59",
    "bmc": 2.18,
    "smm": 21.2,
    "protein": 7.3,
    "deviceBrand": "InBody_570",
    "bfmControl": "-25.5",
    "ecwOrTbw": "0.392",
    "wholeBodyPhaseAngle50khz": None,
    "basalMetabolicRate": "1309",
    "totalBodyWater": 32.2,
    "minerals": 2.82,
    "waistHipRatio": "0.99",
    "vfl": "20",
    "pbf": "47.0",
    "bodyAge": None,
}

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
- 60分以下：需重点关注，身体负担较重

用"满载的汽车"等比喻，先肯定基础，再指出改善空间。

### 二、负向指标排雷
1. 脂肪超载：计算 fatControl/bfmControl（负值=需减少量）
   - 话术："每天背着近XX斤的大米生活"
   
2. 内脏脂肪：读取 vfl（1-9正常，10-14警惕，≥15高危）
   - 话术："给肝脏穿了一件厚羽绒服"
   
3. 肌肉储备：读取 smm、muscleControl
   - 话术："发动机变小，热量难消耗"

### 三、正向资本盘点
1. 相位角（wholeBodyPhaseAngle50khz）：
   - 如果有数据（>0），高=细胞年轻。话术："电池健康度，抗老能力超强"
   - 如果数据缺失，可从骨骼、水分比率等方面挖掘优势
   
2. 骨骼（bmc/minerals）：好=能承受运动
   - 话术："骨架结实，行动自由度极高"

3. 水分比率（ecwOrTbw）：正常范围0.360-0.390
   - 低=无炎症，减脂快
   - 高=可能有水肿或炎症

### 四、四维耦合改善策略
（基于国家级《健康生活方式指导原则》，必须结合用户前面的具体数据（如肌肉缺口、内脏脂肪等级）给出个性化建议。注意：每个维度只输出最核心的1条精准建议，绝不发散，不要长篇大论罗列）
1. 睡眠（良好睡眠）
   - 核心1条：每晚7-8小时高质量睡眠，睡前避免刷手机、喝咖啡。
2. 情绪（积极心态）
   - 核心1条：推荐社群参与（舞蹈团，健步走，合唱团，八段锦队，马拉松跑团等）。数据证明：社群参与者的身心健康、快乐幸福指数比非参与者高出1.5倍。
3. 运动（合理运动）
   - 核心1条：结合用户骨骼肌或脂肪超标情况，精准给出一个运动处方（如：针对脂肪超标推荐每周3-4次快走/游泳；或针对肌肉缺口推荐弹力带/扶椅深蹲）。不要分阶段长篇大论。
4. 饮食（均衡营养）
   - 核心1条：结合代谢或脂肪情况，给出一条核心饮食搭配。例如：代谢低则优先补充植物蛋白/小分子肽减轻脏器压力（绝对不要推荐乳清蛋白）；或补充黄酮多酚类水果蔬菜抗炎；或用深海鱼油搭配卵磷脂协同清除并运输脂肪；或将主食替换为低GI粗粮。只选最切中痛点的一条展开。

### 五、课程引流
（必须严格且唯一地推荐以下指定课程，绝对不要发散推荐其他任何方案、套餐或会员）
- 唯一推荐课程：《轻松"享瘦" 营养先行-现代人体质量管理观念6课》
- 权威背书：与国务院发展研究中心合作的《社群体重管理研究白皮书》已正式发布。

## 输出格式
直接输出解读内容，使用中文，按五个大模块分段（一至三为数据解读，四为四维策略，五为课程推荐），每个模块有标题。语气亲切自然，像朋友聊天。"""

def generate_user_prompt(data):
    sex_text = "女性" if str(data.get("sex", "1")) == "2" else "男性"
    
    return f"""请解读以下 InBody 体测报告数据，输出人性化、接地气的解读报告。

## 用户基础信息
- 年龄：{data.get('age', '未知')} 岁
- 性别：{sex_text}
- 身高：{data.get('height', '未知')} cm
- 体重：{data.get('weight', '未知')} kg
- 测量时间：{data.get('measureEpochMilli', '未知')}

## 核心指标
- InBody 得分：{data.get('score', '未知')} 分
- BMI：{data.get('bmi', '未知')}
- 体脂率：{data.get('pbf', '未知')}%
- 体脂肪量：{data.get('bfm', '未知')} kg
- 脂肪控制：{data.get('fatControl', data.get('bfmControl', '未知'))} kg
- 骨骼肌：{data.get('smm', '未知')} kg
- 肌肉控制：{data.get('muscleControl', data.get('ffmControl', 0))} kg
- 骨矿物质：{data.get('bmc', '未知')} kg
- 相位角：{data.get('wholeBodyPhaseAngle50khz', '未测量')}
- 内脏脂肪等级：{data.get('vfl', data.get('vfaLevel', '未知'))}
- 细胞外水分比率：{data.get('ecwOrTbw', '未知')}
- 基础代谢率：{data.get('bmr', data.get('basalMetabolicRate', '未知'))} kcal
- 腰臀比：{data.get('whr', data.get('waistHipRatio', '未知'))}

## 请按以下格式输出解读报告：
一、分数解读
二、负向指标分析
三、正向资本盘点
四、四维耦合改善策略
五、课程推荐"""


def main():
    print("=" * 60)
    print("InBody 体测报告智能解读测试")
    print("样例数据：58岁女性，BMI 34.1，得分59分，脂肪超标25.5kg")
    print("=" * 60)
    print()
    
    user_prompt = generate_user_prompt(sample_data)
    
    print("用户提示词：")
    print("-" * 60)
    print(user_prompt)
    print()
    print("-" * 60)
    print()
    
    print("系统提示词和用户提示词已准备好。")
    print("请将以上内容复制到大模型进行测试。")
    print()
    
    # 输出到文件
    with open("/workspace/projects/inbody-report-analyzer/test_prompts.txt", "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("系统提示词\n")
        f.write("=" * 60 + "\n")
        f.write(SYSTEM_PROMPT)
        f.write("\n\n")
        f.write("=" * 60 + "\n")
        f.write("用户提示词\n")
        f.write("=" * 60 + "\n")
        f.write(user_prompt)
    
    print("提示词已保存到: /workspace/projects/inbody-report-analyzer/test_prompts.txt")


if __name__ == "__main__":
    main()
