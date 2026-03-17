#!/usr/bin/env python3
"""
增强版批判性评价工具
支持基于全文的深度评价
"""

import sys
import json
from typing import Dict, List

# 扩展的评价清单，包含全文分析要点
FULLTEXT_APPRAISAL_CHECKLISTS = {
    "RCT": {
        "name": "随机对照试验 (Randomized Controlled Trial)",
        "sections": {
            "title_abstract": [
                {"id": "title_identifies_design", "question": "标题是否明确标识研究设计？", "weight": "optional"},
                {"id": "abstract_structured", "question": "摘要是否使用结构化格式？", "weight": "optional"},
                {"id": "abstract_complete", "question": "摘要是否包含目的、方法、结果、结论？", "weight": "essential"}
            ],
            "introduction": [
                {"id": "background_rationale", "question": "背景和理论基础是否充分？", "weight": "essential"},
                {"id": "objectives_clear", "question": "研究目的是否明确？", "weight": "essential"},
                {"id": "hypothesis_stated", "question": "假设是否清晰陈述？", "weight": "important"}
            ],
            "methods": [
                {"id": "design_appropriate", "question": "研究设计是否适合研究问题？", "weight": "essential"},
                {"id": "participants_clear", "question": "研究对象纳入/排除标准是否明确？", "weight": "essential"},
                {"id": "randomization_method", "question": "随机化方法是否恰当？", "weight": "essential"},
                {"id": "allocation_concealment", "question": "分配隐藏是否充分？", "weight": "essential"},
                {"id": "blinding_described", "question": "盲法（受试者/干预者/评估者）是否描述清楚？", "weight": "essential"},
                {"id": "sample_size_calculation", "question": "是否报告样本量计算？", "weight": "important"},
                {"id": "intervention_detailed", "question": "干预措施描述是否足够详细以重复？", "weight": "essential"},
                {"id": "outcomes_defined", "question": "主要和次要结局指标是否预定义？", "weight": "essential"},
                {"id": "statistical_methods", "question": "统计方法是否适合研究设计？", "weight": "essential"}
            ],
            "results": [
                {"id": "participant_flow", "question": "参与者流程图是否报告？", "weight": "essential"},
                {"id": "baseline_comparable", "question": "基线特征是否可比？", "weight": "essential"},
                {"id": "numbers_analyzed", "question": "每个分析的样本量是否报告？", "weight": "essential"},
                {"id": "estimates_precision", "question": "效应估计是否报告精确度（95%CI）？", "weight": "essential"},
                {"id": "harms_reported", "question": "不良事件是否全面报告？", "weight": "important"},
                {"id": "ancillary_analyses", "question": "次要分析和亚组分析是否预先计划？", "weight": "important"}
            ],
            "discussion": [
                {"id": "interpretation_balanced", "question": "结果解释是否考虑了偏倚来源？", "weight": "essential"},
                {"id": "generalizability", "question": "结果的可推广性是否讨论？", "weight": "important"},
                {"id": "evidence_synthesis", "question": "是否结合现有证据进行解释？", "weight": "important"}
            ],
            "other": [
                {"id": "protocol_available", "question": "研究方案是否可获取？", "weight": "important"},
                {"id": "registration", "question": "研究是否注册？", "weight": "important"},
                {"id": "funding_disclosed", "question": "资金来源和潜在利益冲突是否声明？", "weight": "essential"}
            ]
        }
    },
    "systematic_review": {
        "name": "系统综述/Meta分析",
        "sections": {
            "title_abstract": [
                {"id": "identifies_sr", "question": "标题是否明确标识为系统综述/Meta分析？", "weight": "essential"},
                {"id": "pico_in_abstract", "question": "摘要是否描述PICO要素？", "weight": "essential"}
            ],
            "introduction": [
                {"id": "rationale_clear", "question": "综述理由是否清楚？", "weight": "essential"},
                {"id": "objectives_pico", "question": "研究问题是否使用PICO框架表述？", "weight": "essential"},
                {"id": "protocol_registered", "question": "综述方案是否预先注册？", "weight": "important"}
            ],
            "methods": [
                {"id": "inclusion_criteria", "question": "纳入标准是否明确？", "weight": "essential"},
                {"id": "search_sources", "question": "检索的数据库和其他来源是否报告？", "weight": "essential"},
                {"id": "search_dates", "question": "检索日期是否报告？", "weight": "essential"},
                {"id": "full_search_strategy", "question": "完整检索策略是否提供或附加？", "weight": "essential"},
                {"id": "study_selection", "question": "研究选择过程是否描述？", "weight": "essential"},
                {"id": "data_extraction", "question": "数据提取方法是否描述？", "weight": "essential"},
                {"id": "risk_of_bias_tool", "question": "偏倚风险评估工具是否报告？", "weight": "essential"},
                {"id": "synthesis_methods", "question": "合成方法是否适合研究问题和数据？", "weight": "essential"},
                {"id": "heterogeneity_assessment", "question": "异质性评估方法是否描述？", "weight": "essential"},
                {"id": "sensitivity_analyses", "question": "敏感性分析是否计划？", "weight": "important"}
            ],
            "results": [
                {"id": "selection_flow", "question": "研究选择流程图是否报告（PRISMA）？", "weight": "essential"},
                {"id": "study_characteristics", "question": "纳入研究特征是否描述？", "weight": "essential"},
                {"id": "rob_results", "question": "每个研究的偏倚风险结果是否报告？", "weight": "essential"},
                {"id": "individual_study_results", "question": "每个研究的结果是否呈现？", "weight": "essential"},
                {"id": "synthesis_results", "question": "合成结果是否报告？", "weight": "essential"},
                {"id": "heterogeneity_reported", "question": "异质性调查结果是否报告？", "weight": "essential"},
                {"id": "sensitivity_results", "question": "敏感性分析结果是否报告？", "weight": "important"},
                {"id": "publication_bias", "question": "发表偏倚是否评估和讨论？", "weight": "important"}
            ],
            "discussion": [
                {"id": "limitations_review", "question": "综述局限性是否讨论？", "weight": "essential"},
                {"id": "limitations_evidence", "question": "证据局限性是否讨论？", "weight": "essential"},
                {"id": "conclusions_appropriate", "question": "结论是否基于证据？", "weight": "essential"}
            ]
        }
    },
    "observational": {
        "name": "观察性研究（队列/病例对照/横断面）",
        "sections": {
            "methods": [
                {"id": "study_design_clear", "question": "研究设计类型是否明确说明？", "weight": "essential"},
                {"id": "setting_described", "question": "研究背景（地点、时间）是否描述？", "weight": "essential"},
                {"id": "participants_detailed", "question": "参与者特征和来源是否详细描述？", "weight": "essential"},
                {"id": "exposure_defined", "question": "暴露/干预定义是否清楚？", "weight": "essential"},
                {"id": "outcome_defined", "question": "结局定义是否清楚？", "weight": "essential"},
                {"id": "confounders_identified", "question": "潜在混杂因素是否识别？", "weight": "essential"},
                {"id": "sample_size_justified", "question": "样本量是否有合理性说明？", "weight": "important"}
            ],
            "results": [
                {"id": "participants_described", "question": "参与者数量和特征是否描述？", "weight": "essential"},
                {"id": "followup_adequate", "question": "随访时间是否足够？", "weight": "essential"},
                {"id": "missing_data_handled", "question": "缺失数据处理是否描述？", "weight": "important"},
                {"id": "confounding_adjusted", "question": "是否调整混杂因素？", "weight": "essential"}
            ]
        }
    }
}


def generate_fulltext_appraisal(study_type: str) -> Dict:
    """生成全文批判性评价模板"""
    template = FULLTEXT_APPRAISAL_CHECKLISTS.get(study_type, FULLTEXT_APPRAISAL_CHECKLISTS["observational"])
    
    result = {
        "study_type": study_type,
        "study_type_name": template["name"],
        "overall_score": None,
        "overall_judgment": None,  # "low_risk", "some_concerns", "high_risk"
        "sections": {}
    }
    
    for section_name, items in template["sections"].items():
        result["sections"][section_name] = {
            "items": [
                {
                    "id": item["id"],
                    "question": item["question"],
                    "weight": item["weight"],
                    "answer": None,
                    "notes": ""
                }
                for item in items
            ],
            "section_score": None
        }
    
    return result


def calculate_quality_score(appraisal: Dict) -> Dict:
    """计算质量评分"""
    total_essential = 0
    answered_essential = 0
    total_important = 0
    answered_important = 0
    
    for section in appraisal.get("sections", {}).values():
        for item in section.get("items", []):
            weight = item.get("weight", "optional")
            answer = item.get("answer")
            
            if weight == "essential":
                total_essential += 1
                if answer in ["是", "yes", "y"]:
                    answered_essential += 1
            elif weight == "important":
                total_important += 1
                if answer in ["是", "yes", "y"]:
                    answered_important += 1
    
    essential_score = (answered_essential / total_essential * 100) if total_essential > 0 else 0
    important_score = (answered_important / total_important * 100) if total_important > 0 else 0
    
    # 总体判断
    if essential_score >= 90:
        judgment = "low_risk"
        judgment_text = "低偏倚风险 - 高质量研究"
    elif essential_score >= 70:
        judgment = "some_concerns"
        judgment_text = "存在一些担忧 - 中等质量研究"
    else:
        judgment = "high_risk"
        judgment_text = "高偏倚风险 - 需谨慎解读"
    
    return {
        "essential_items": {
            "answered": answered_essential,
            "total": total_essential,
            "score": round(essential_score, 1)
        },
        "important_items": {
            "answered": answered_important,
            "total": total_important,
            "score": round(important_score, 1)
        },
        "overall_judgment": judgment,
        "overall_judgment_text": judgment_text
    }


def format_fulltext_appraisal(appraisal: Dict) -> str:
    """格式化评价报告"""
    lines = []
    lines.append(f"# 全文批判性评价报告: {appraisal['study_type_name']}")
    lines.append("")
    
    for section_name, section_data in appraisal.get("sections", {}).items():
        section_title = section_name.replace("_", " ").title()
        lines.append(f"## {section_title}")
        lines.append("")
        
        for item in section_data.get("items", []):
            weight_label = {"essential": "【必需】", "important": "【重要】", "optional": "【可选】"}.get(
                item.get("weight", ""), ""
            )
            answer = item.get("answer", "未评价")
            lines.append(f"### {item['id']}")
            lines.append(f"{weight_label} {item['question']}")
            lines.append(f"**回答**: {answer}")
            if item.get("notes"):
                lines.append(f"**备注**: {item['notes']}")
            lines.append("")
    
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: fulltext_appraisal.py <study_type> [fulltext_analysis_json]", file=sys.stderr)
        print("  study_type: RCT, systematic_review, observational", file=sys.stderr)
        print("  fulltext_analysis_json: 可选，预填充的分析结果", file=sys.stderr)
        sys.exit(1)
    
    study_type = sys.argv[1]
    
    appraisal = generate_fulltext_appraisal(study_type)
    
    # 如果有预填充数据
    if len(sys.argv) > 2:
        try:
            prefilled = json.loads(sys.argv[2])
            # 这里可以添加预填充逻辑
        except json.JSONDecodeError:
            pass
    
    print(json.dumps(appraisal, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
