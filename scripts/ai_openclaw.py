#!/usr/bin/env python3
"""
AI 辅助医学文献分析 - OpenClaw 集成版
通过 mmx 调用 MiniMax LLM
"""

import sys
import json
import subprocess
import re
from typing import Dict


DEFAULT_MODEL = "MiniMax-M2.7"


def mmx_chat(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """调用 mmx text chat"""
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


def extract_json(text: str) -> Dict:
    """从响应中提取 JSON"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    return {"raw": text}


def analyze_paper(title: str, abstract: str, full_text: str = "") -> Dict:
    """全面分析单篇文献"""
    text = f"标题: {title}\n\n摘要: {abstract}"
    if full_text:
        text += f"\n\n全文:\n{full_text}"

    prompt = f"""作为循证医学专家，分析这篇医学文献，输出有效 JSON：

{{
  "pico": {{
    "population": "研究人群",
    "intervention": "干预措施",
    "comparison": "对照组",
    "outcomes": ["结局"],
    "study_design": "RCT/队列/病例对照"
  }},
  "one_sentence_summary": "一句话发现",
  "quality": {{
    "evidence_quality": "高/中/低/极低",
    "key_strengths": ["优点"],
    "key_limitations": ["局限"]
  }},
  "recommendation": "临床推荐"
}}

文献：
{text}

只输出 JSON。"""

    try:
        response = mmx_chat(prompt)
        result = extract_json(response)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    if len(sys.argv) < 3:
        print("用法: ai_openclaw.py analyze <标题> <摘要>", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "analyze":
        title = sys.argv[2]
        abstract = sys.argv[3] if len(sys.argv) > 3 else ""
        result = analyze_paper(title, abstract)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"未知命令: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
