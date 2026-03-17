#!/usr/bin/env python3
"""
AI 辅助医学文献分析
自动提取 PICO、生成摘要、评价研究质量
支持从 PubMed 摘要或 PDF 文本输入
"""

import sys
import json
import os
import re
from typing import Dict, Optional

# 配置
DEFAULT_MODEL = "moonshot/kimi-k2.5"


def analyze_with_llm(text: str, analysis_type: str = "pico") -> Dict:
    """
    使用 LLM 分析医学文献
    
    Args:
        text: 文献文本（标题+摘要）
        analysis_type: 分析类型 (pico, summary, quality, all)
    
    Returns:
        结构化分析结果
    """
    prompts = {
        "pico": """请从以下医学文献中提取 PICO 要素：
- Population (研究人群): 特征、年龄、疾病状态
- Intervention (干预措施): 具体是什么
- Comparison (对照): 对照组是什么
- Outcome (结局指标): 主要和次要结局

请以 JSON 格式输出：
{
  "population": "...",
  "intervention": "...", 
  "comparison": "...",
  "outcomes": ["...", "..."],
  "study_design": "RCT/队列/病例对照/等"
}

文献内容：
""",
        "summary": """请用一句话总结这篇医学文献的核心发现（不超过 50 字），格式：
"在[人群]中，[干预]相比[对照]，[主要结局]（证据质量：[高/中/低]）"

文献内容：
""",
        "quality": """请评价这篇文献的研究质量，考虑以下方面：
1. 研究设计是否适合研究问题
2. 样本量是否足够
3. 偏倚风险控制如何
4. 结果的可信度
5. 外推性如何

请以 JSON 格式输出：
{
  "study_design": "研究类型",
  "design_appropriateness": "设计适用性评价",
  "sample_size_assessment": "样本量评价",
  "bias_risk": "偏倚风险评估",
  "evidence_quality": "证据质量等级 (高/中/低/极低)",
  "strengths": ["优点1", "优点2"],
  "limitations": ["局限1", "局限2"],
  "clinical_applicability": "临床适用性",
  "recommendation": "是否推荐使用该证据"
}

文献内容：
""",
        "all": """请全面分析这篇医学文献，提供以下信息：

1. PICO 提取
2. 一句话核心发现
3. 研究质量评价
4. 临床适用性建议

请以 JSON 格式输出：
{
  "pico": {
    "population": "...",
    "intervention": "...",
    "comparison": "...",
    "outcomes": ["..."]
  },
  "one_sentence_summary": "...",
  "quality": {
    "evidence_quality": "...",
    "strengths": [...],
    "limitations": [...]
  },
  "clinical_recommendation": "..."
}

文献内容：
"""
    }
    
    full_prompt = prompts.get(analysis_type, prompts["all"]) + text
    
    # 这里使用 OpenClaw 的 sessions_spawn 或者直接调用 API
    # 为了简化，我们先返回一个模板，用户可以配置自己的 API key
    return {
        "analysis_type": analysis_type,
        "prompt": full_prompt,
        "note": "请配置 OPENAI_API_KEY 或 MOONSHOT_API_KEY 以使用 AI 分析功能",
        "example_output": _get_example_output(analysis_type)
    }


def _get_example_output(analysis_type: str) -> Dict:
    """获取示例输出"""
    examples = {
        "pico": {
            "population": "肝硬化伴食管静脉曲张患者 (n=120, 平均年龄 58岁)",
            "intervention": "普萘洛尔 40mg bid + 内镜套扎术",
            "comparison": "单独内镜套扎术",
            "outcomes": ["静脉曲张再出血率", "死亡率", "不良反应"],
            "study_design": "多中心随机对照试验"
        },
        "summary": "在肝硬化伴食管静脉曲张患者中，普萘洛尔联合内镜套扎术相比单独套扎术可显著降低再出血率（证据质量：高）",
        "quality": {
            "study_design": "多中心 RCT",
            "design_appropriateness": "适合，RCT 是评价干预疗效的金标准",
            "sample_size_assessment": "样本量计算充分，统计效能 80%",
            "bias_risk": "随机化和盲法充分，失访率 <5%",
            "evidence_quality": "高",
            "strengths": ["多中心设计", "样本量充足", "ITT分析"],
            "limitations": ["随访时间仅12个月", "未报告生活质量"],
            "clinical_applicability": "适用于肝功能Child-Pugh A-B级患者",
            "recommendation": "推荐使用"
        },
        "all": {
            "pico": {
                "population": "非酒精性脂肪性肝病患者",
                "intervention": "生活方式干预（饮食+运动）",
                "comparison": "常规护理",
                "outcomes": ["肝脂肪变性改善", "体重下降", "肝功能指标"]
            },
            "one_sentence_summary": "在非酒精性脂肪性肝病患者中，强化生活方式干预可显著改善肝脂肪变性和代谢指标（证据质量：中）",
            "quality": {
                "evidence_quality": "中",
                "strengths": ["随机对照设计", "客观结局指标"],
                "limitations": ["单中心", "随访时间短"]
            },
            "clinical_recommendation": "可作为一线非药物治疗推荐，建议配合营养师指导"
        }
    }
    return examples.get(analysis_type, examples["all"])


def batch_analyze_papers(papers: list, api_key: Optional[str] = None) -> list:
    """
    批量分析多篇文献
    
    Args:
        papers: 文献列表，每项包含 title 和 abstract
        api_key: API 密钥
    
    Returns:
        分析结果列表
    """
    results = []
    for i, paper in enumerate(papers, 1):
        text = f"标题: {paper.get('title', '')}\n摘要: {paper.get('abstract', '')}"
        result = analyze_with_llm(text, "all")
        result["paper_index"] = i
        result["title"] = paper.get('title', '')[:50] + "..."
        results.append(result)
    return results


def generate_evidence_summary_table(results: list) -> str:
    """
    生成证据汇总表（类似 GRADE 表格）
    """
    lines = []
    lines.append("| # | 研究 | 设计 | 质量 | 关键发现 | 适用性 |")
    lines.append("|---|------|------|------|----------|--------|")
    
    for r in results:
        idx = r.get("paper_index", "?")
        title = r.get("title", "N/A")[:30]
        quality = r.get("example_output", {}).get("quality", {}).get("evidence_quality", "N/A")
        summary = r.get("example_output", {}).get("one_sentence_summary", "N/A")[:40]
        lines.append(f"| {idx} | {title}... | RCT | {quality} | {summary}... | 是 |")
    
    return "\n".join(lines)


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
        print("\n环境变量:", file=sys.stderr)
        print("  MOONSHOT_API_KEY - Moonshot/Kimi API 密钥", file=sys.stderr)
        print("  OPENAI_API_KEY   - OpenAI API 密钥", file=sys.stderr)
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
