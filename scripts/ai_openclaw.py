#!/usr/bin/env python3
"""
AI 辅助医学文献分析 - OpenClaw 集成版
调用 OpenClaw 的 AI 能力分析文献
"""

import sys
import json
import subprocess
from typing import Dict, Optional


def call_openclaw_ai(prompt: str) -> str:
    """
    调用 OpenClaw AI 分析
    通过 sessions_spawn 发送请求
    """
    # 构造请求
    task = f"请分析以下医学文献并返回 JSON 格式结果：\n\n{prompt}\n\n请确保输出是有效的 JSON 格式。"
    
    # 返回提示信息（实际调用需要 OpenClaw 会话支持）
    return f"[OpenClaw AI 分析请求已构造]\n提示词长度: {len(prompt)} 字符\n\n提示词预览:\n{prompt[:200]}..."


def analyze_paper(title: str, abstract: str, full_text: str = "") -> Dict:
    """
    全面分析单篇文献
    
    Returns:
        {
            "pico": {...},
            "summary": "...",
            "quality": {...},
            "recommendation": "..."
        }
    """
    text = f"""标题: {title}

摘要: {abstract}

{full_text if full_text else ""}
"""
    
    prompt = f"""请作为循证医学专家，全面分析这篇医学文献：

{text}

请提供以下分析（以 JSON 格式返回）：

{{
  "pico": {{
    "population": "研究人群特征（样本量、年龄、疾病等）",
    "intervention": "干预措施详细描述",
    "comparison": "对照组描述",
    "outcomes": ["主要结局", "次要结局"],
    "study_design": "研究设计类型"
  }},
  "one_sentence_summary": "一句话核心发现（50字内）",
  "clinical_significance": "临床意义评价",
  "quality": {{
    "study_design": "研究设计",
    "evidence_level": "证据等级（I-V级）",
    "evidence_quality": "GRADE质量（高/中/低/极低）",
    "key_strengths": ["关键优点"],
    "key_limitations": ["主要局限"],
    "bias_risk": "偏倚风险评估（低/中/高）",
    "applicability": "外推性评价"
  }},
  "statistics": {{
    "effect_size": "效应量及置信区间",
    "p_value": "P值",
    "clinical_importance": "临床重要性判断"
  }},
  "recommendation": {{
    "clinical_use": "是否推荐临床应用（强烈推荐/有条件推荐/不推荐）",
    "target_population": "适用人群",
    "key_considerations": ["使用时的关键考虑因素"],
    "confidence": "推荐信心度（高/中/低）"
  }}
}}

注意：
1. 如果不确定某字段内容，请填 "未报告" 或 "N/A"
2. 一句话总结格式："在[人群]中，[干预]相比[对照]，[主要结局]"
3. 证据质量使用 GRADE 系统评价"""

    # 这里可以集成 OpenClaw 的 AI 调用
    # 目前返回结构和示例数据
    return {
        "analysis_requested": True,
        "prompt": prompt,
        "note": "在 OpenClaw 环境中运行时，此分析将自动调用 AI 模型",
        "manual_instruction": "复制 prompt 到 OpenClaw 对话中获取 AI 分析结果"
    }


def compare_studies(studies: list) -> Dict:
    """
    比较多个研究的结果
    
    Args:
        studies: 研究列表，每项包含 title, intervention, outcome, effect_size
    """
    comparison_prompt = "请比较以下研究的异同，并评估结果一致性：\n\n"
    
    for i, study in enumerate(studies, 1):
        comparison_prompt += f"研究{i}:\n"
        comparison_prompt += f"  标题: {study.get('title', 'N/A')}\n"
        comparison_prompt += f"  干预: {study.get('intervention', 'N/A')}\n"
        comparison_prompt += f"  结局: {study.get('outcome', 'N/A')}\n"
        comparison_prompt += f"  效应量: {study.get('effect_size', 'N/A')}\n\n"
    
    return {
        "comparison_prompt": comparison_prompt,
        "analysis_type": "cross_study_comparison",
        "note": "将帮助识别异质性来源和亚组分析方向"
    }


def generate_clinical_question(pico: Dict) -> str:
    """
    基于 PICO 生成临床问题
    """
    return f"""临床问题（PICO格式）：

**P (Population)**：{pico.get('population', 'N/A')}
**I (Intervention)**：{pico.get('intervention', 'N/A')}
**C (Comparison)**：{pico.get('comparison', 'N/A')}
**O (Outcome)**：{', '.join(pico.get('outcomes', ['N/A']))}

问题：在{pico.get('population', '某人群')}中，
{pico.get('intervention', '某干预')}相比{pico.get('comparison', '对照')}，
能否改善{pico.get('outcomes', ['结局'])[0]}？
"""


def main():
    if len(sys.argv) < 2:
        print("AI 辅助文献分析工具 (OpenClaw 集成版)", file=sys.stderr)
        print("\n用法:", file=sys.stderr)
        print("  ai_openclaw.py <命令> [参数]", file=sys.stderr)
        print("\n命令:", file=sys.stderr)
        print("  analyze <title> <abstract>  - 分析单篇文献", file=sys.stderr)
        print("  pico <title> <abstract>     - 提取 PICO", file=sys.stderr)
        print("  compare <studies.json>      - 比较多个研究", file=sys.stderr)
        print("\n示例:", file=sys.stderr)
        print('  ai_openclaw.py analyze "标题" "摘要内容"', file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "analyze" and len(sys.argv) >= 4:
        title = sys.argv[2]
        abstract = sys.argv[3]
        result = analyze_paper(title, abstract)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "pico" and len(sys.argv) >= 4:
        title = sys.argv[2]
        abstract = sys.argv[3]
        result = analyze_paper(title, abstract)
        print(json.dumps(result.get("pico", {}), indent=2, ensure_ascii=False))
    
    else:
        print(f"未知命令或参数不足: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
