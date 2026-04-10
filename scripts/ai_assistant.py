#!/usr/bin/env python3
"""
AI 辅助医学文献分析
通过 mmx (MiniMax CLI) 调用 LLM 分析医学文献
支持 PICO 提取、质量评价、临床建议
"""

import sys
import json
import subprocess
import os
import re
from typing import Dict, Optional

DEFAULT_MODEL = "MiniMax-M2.7"


def mmx_chat(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    调用 mmx text chat 并返回纯文本响应
    """
    result = subprocess.run(
        ["mmx", "text", "chat",
         "--model", model,
         "--message", prompt,
         "--non-interactive",
         "--quiet",
         "--output", "text"],
        capture_output=True,
        text=True,
        timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"mmx 调用失败: {result.stderr}")
    return result.stdout.strip()


def extract_json_from_response(text: str) -> Optional[Dict]:
    """从响应中提取 JSON"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试从 markdown 代码块中提取
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    return None


def analyze_with_llm(text: str, analysis_type: str = "all") -> Dict:
    """
    使用 LLM 分析医学文献

    Args:
        text: 文献文本（标题+摘要）
        analysis_type: 分析类型 (pico, summary, quality, all)

    Returns:
        结构化分析结果
    """

    prompts = {
        "pico": f"""请从以下医学文献中提取 PICO 要素，输出有效 JSON：

{{
  "population": "研究人群特征（样本量、年龄、疾病等）",
  "intervention": "干预措施详细描述",
  "comparison": "对照组描述",
  "outcomes": ["主要结局", "次要结局"],
  "study_design": "研究设计类型"
}}

文献内容：
{text}

只输出 JSON，不要其他文字。""",

        "summary": f"""用一句话总结这篇医学文献的核心发现（不超过 50 字），格式：
"在[人群]中，[干预]相比[对照]，[主要结局]（证据质量：[高/中/低]）"

文献内容：
{text}

只输出这句话，不要其他文字。""",

        "quality": f"""请评价这篇文献的研究质量，输出有效 JSON：

{{
  "study_design": "研究类型",
  "evidence_level": "证据等级（I-V级）",
  "evidence_quality": "GRADE质量（高/中/低/极低）",
  "key_strengths": ["优点1", "优点2"],
  "key_limitations": ["局限1", "局限2"],
  "bias_risk": "偏倚风险（低/中/高）",
  "clinical_applicability": "临床适用性"
}}

文献内容：
{text}

只输出 JSON，不要其他文字。""",

        "all": f"""作为循证医学专家，全面分析这篇医学文献，输出有效 JSON：

{{
  "pico": {{
    "population": "研究人群",
    "intervention": "干预措施",
    "comparison": "对照组",
    "outcomes": ["结局1", "结局2"],
    "study_design": "RCT/队列/病例对照等"
  }},
  "one_sentence_summary": "一句话核心发现",
  "quality": {{
    "evidence_quality": "高/中/低/极低",
    "key_strengths": ["优点"],
    "key_limitations": ["局限"]
  }},
  "clinical_recommendation": "临床推荐建议"
}}

文献内容：
{text}

只输出 JSON，不要其他文字。"""
    }

    prompt = prompts.get(analysis_type, prompts["all"])

    try:
        response = mmx_chat(prompt)
        result = extract_json_from_response(response)

        if result:
            return {
                "status": "success",
                "analysis_type": analysis_type,
                "result": result,
                "raw_response": response
            }
        else:
            return {
                "status": "parse_error",
                "analysis_type": analysis_type,
                "raw_response": response,
                "error": "无法解析 JSON 响应"
            }
    except Exception as e:
        return {
            "status": "error",
            "analysis_type": analysis_type,
            "error": str(e)
        }


def main():
    if len(sys.argv) < 2:
        print("AI 辅助医学文献分析工具", file=sys.stderr)
        print("\n用法:", file=sys.stderr)
        print("  ai_assistant.py <文献文件> [分析类型]", file=sys.stderr)
        print("\n分析类型:", file=sys.stderr)
        print("  pico     - 提取 PICO 要素", file=sys.stderr)
        print("  summary  - 生成一句话总结", file=sys.stderr)
        print("  quality  - 研究质量评价", file=sys.stderr)
        print("  all      - 全面分析（默认）", file=sys.stderr)
        print("\n示例:", file=sys.stderr)
        print('  ai_assistant.py paper.txt all', file=sys.stderr)
        print('  ai_assistant.py paper.txt pico', file=sys.stderr)
        print("\n前提: 已安装 mmx CLI 并登录 (mmx auth login)", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    analysis_type = sys.argv[2] if len(sys.argv) > 2 else "all"

    # 读取文献内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"错误: 文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取文件失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 分析
    result = analyze_with_llm(text, analysis_type)

    # 输出结果
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
