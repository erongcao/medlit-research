#!/usr/bin/env python3
"""
医学文献批判性评价工具
基于研究设计类型提供结构化评价框架
"""

import sys
import json
from typing import Dict, List

# 不同研究设计的评价清单
CRITICAL_APPRAISAL_CHECKLISTS = {
    "RCT": {
        "name": "随机对照试验 (Randomized Controlled Trial)",
        "questions": [
            {"id": "randomization", "question": "随机化方法是否恰当？", "details": "是否使用计算机随机数生成器、随机数字表等方法？分配隐藏是否充分？"},
            {"id": "blinding", "question": "是否采用盲法？", "details": "受试者、干预提供者、结局评估者是否对分组情况不知情？"},
            {"id": "sample_size", "question": "样本量是否足够？", "details": "是否进行了样本量计算？效应估计的精确度如何？"},
            {"id": "baseline", "question": "基线是否可比？", "details": "各组间年龄、性别、疾病严重程度等基线特征是否相似？"},
            {"id": "intention_to_treat", "question": "是否采用意向性治疗分析？", "details": "是否对所有随机化受试者进行分析，无论是否完成研究？"},
            {"id": "followup", "question": "随访是否完整？", "details": "失访率是否<20%？失访原因是否报告？"},
            {"id": "outcome_measurement", "question": "结局指标测量是否可靠？", "details": "主要结局是否预先设定？测量方法是否标准化？"},
            {"id": "conflicts", "question": "是否存在利益冲突？", "details": "资金来源是否声明？是否有其他潜在偏倚来源？"}
        ]
    },
    "cohort": {
        "name": "队列研究 (Cohort Study)",
        "questions": [
            {"id": "exposure_definition", "question": "暴露定义是否明确？", "details": "暴露组和非暴露组的定义是否清晰、可重现？"},
            {"id": "outcome_blind", "question": "结局评估者是否对暴露状态不知情？", "details": "是否采用盲法评估结局以避免测量偏倚？"},
            {"id": "followup_adequate", "question": "随访是否充分？", "details": "随访时间是否足够长？随访率是否>80%？"},
            {"id": "confounding", "question": "是否控制混杂因素？", "details": "是否识别并调整重要的混杂变量？"},
            {"id": "selection_bias", "question": "是否存在选择偏倚？", "details": "研究对象选择方式是否可能导致偏倚？"},
            {"id": "generalizability", "question": "结果是否具有外推性？", "details": "研究人群是否代表目标人群？"}
        ]
    },
    "case_control": {
        "name": "病例对照研究 (Case-Control Study)",
        "questions": [
            {"id": "case_definition", "question": "病例定义是否明确？", "details": "诊断标准是否客观、可验证？"},
            {"id": "control_selection", "question": "对照选择是否恰当？", "details": "对照是否来自与病例相同的源人群？"},
            {"id": "recall_bias", "question": "是否存在回忆偏倚？", "details": "病例组和对照组回忆暴露信息的方式是否相似？"},
            {"id": "temporality", "question": "时间顺序是否明确？", "details": "暴露是否确实发生在结局之前？"},
            {"id": "confounding_control", "question": "混杂因素控制是否充分？", "details": "是否匹配或调整重要混杂因素？"}
        ]
    },
    "systematic_review": {
        "name": "系统综述/Meta分析",
        "questions": [
            {"id": "question_clear", "question": "研究问题是否明确？", "details": "是否使用PICO框架？是否预先注册方案？"},
            {"id": "search_comprehensive", "question": "检索是否全面？", "details": "是否检索多个数据库？是否包括灰色文献？"},
            {"id": "selection_bias_risk", "question": "研究选择偏倚风险如何？", "details": "是否两人独立筛选？是否报告排除原因？"},
            {"id": "quality_assessment", "question": "是否进行质量评价？", "details": "是否使用标准化工具（如Cochrane RoB、NOS）？"},
            {"id": "heterogeneity", "question": "异质性如何处理？", "details": "是否进行异质性检验？是否进行亚组分析或敏感性分析？"},
            {"id": "publication_bias", "question": "是否评估发表偏倚？", "details": "是否使用漏斗图或Egger检验？"},
            {"id": "GRADE", "question": "证据质量是否评级？", "details": "是否使用GRADE系统评估证据质量？"}
        ]
    },
    "cross_sectional": {
        "name": "横断面研究 (Cross-Sectional Study)",
        "questions": [
            {"id": "sampling", "question": "抽样方法是否恰当？", "details": "是否随机抽样？样本是否具有代表性？"},
            {"id": "response_rate", "question": "应答率如何？", "details": "应答率是否足够高？无应答是否可能引入偏倚？"},
            {"id": "measurement_validity", "question": "测量工具是否有效？", "details": "使用的测量工具是否经过验证？信度如何？"},
            {"id": "causality", "question": "因果推断是否谨慎？", "details": "横断面数据是否适合回答因果问题？"}
        ]
    },
    "diagnostic": {
        "name": "诊断试验研究 (Diagnostic Study)",
        "questions": [
            {"id": "reference_standard", "question": "金标准是否恰当？", "details": "参考标准是否能准确区分目标疾病？"},
            {"id": "spectrum_bias", "question": "是否存在谱偏倚？", "details": "研究对象是否涵盖疾病严重程度谱？"},
            {"id": "index_test_blind", "question": "待评价试验是否盲法解读？", "details": "待评价试验结果判读是否对金标准结果不知情？"},
            {"id": "applicability", "question": "结果是否适用于我的患者？", "details": "研究人群是否与我的临床实践相似？"}
        ]
    }
}


def get_appraisal_checklist(study_type: str) -> Dict:
    """获取指定研究类型的评价清单"""
    return CRITICAL_APPRAISAL_CHECKLISTS.get(study_type, {
        "name": "通用研究评价",
        "questions": [
            {"id": "study_question", "question": "研究问题是否明确？", "details": "研究目的、假设是否清晰陈述？"},
            {"id": "study_design", "question": "研究设计是否适合研究问题？", "details": "所选设计是否能回答研究问题？"},
            {"id": "methods", "question": "方法是否描述充分？", "details": "能否根据描述重复研究？"},
            {"id": "results", "question": "结果报告是否完整？", "details": "主要和次要结局是否都报告？"},
            {"id": "conclusions", "question": "结论是否得到数据支持？", "details": "推论是否合理？是否过度外推？"}
        ]
    })


def generate_appraisal_report(study_type: str, answers: Dict[str, str] = None) -> Dict:
    """
    生成批判性评价报告模板
    
    Args:
        study_type: 研究类型 (RCT, cohort, case_control, systematic_review, cross_sectional, diagnostic)
        answers: 可选，预填的答案 {question_id: answer}
    
    Returns:
        评价报告字典
    """
    checklist = get_appraisal_checklist(study_type)
    
    report = {
        "study_type": study_type,
        "study_type_name": checklist["name"],
        "overall_assessment": "",
        "questions": []
    }
    
    for q in checklist["questions"]:
        report["questions"].append({
            "id": q["id"],
            "question": q["question"],
            "details": q["details"],
            "answer": answers.get(q["id"], "") if answers else "",
            "notes": ""
        })
    
    return report


def format_appraisal_report(report: Dict) -> str:
    """格式化评价报告为可读文本"""
    lines = []
    lines.append(f"# 批判性评价报告: {report['study_type_name']}")
    lines.append("")
    lines.append("## 评价清单")
    lines.append("")
    
    for i, q in enumerate(report["questions"], 1):
        lines.append(f"### {i}. {q['question']}")
        lines.append(f"**详细说明**: {q['details']}")
        if q.get("answer"):
            lines.append(f"**回答**: {q['answer']}")
        if q.get("notes"):
            lines.append(f"**备注**: {q['notes']}")
        lines.append("")
    
    if report.get("overall_assessment"):
        lines.append("## 总体评价")
        lines.append(report["overall_assessment"])
        lines.append("")
    
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: critical_appraisal.py <study_type> [answers_json]", file=sys.stderr)
        print("  study_type: RCT, cohort, case_control, systematic_review, cross_sectional, diagnostic", file=sys.stderr)
        print("  answers_json: Optional JSON string with answers", file=sys.stderr)
        print("\nExample:", file=sys.stderr)
        print('  critical_appraisal.py RCT', file=sys.stderr)
        sys.exit(1)
    
    study_type = sys.argv[1]
    answers = {}
    
    if len(sys.argv) > 2:
        try:
            answers = json.loads(sys.argv[2])
        except json.JSONDecodeError as e:
            print(f"Error parsing answers JSON: {e}", file=sys.stderr)
            sys.exit(1)
    
    report = generate_appraisal_report(study_type, answers)
    
    # 输出JSON格式
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
