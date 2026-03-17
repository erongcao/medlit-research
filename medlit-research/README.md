# 📚 MedLit Research - 医学文献研究与批判性评价

[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-blue)](https://github.com/openclaw/openclaw)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 医学文献检索、批判性评价与综合分析工具，支持循证医学实践和临床决策。

[English](#english) | [中文](#中文)

---

## 📋 功能概览

| 功能模块 | 描述 | 状态 |
|---------|------|------|
| 🔍 **PubMed检索** | NCBI E-utilities API文献检索 | ✅ |
| 📊 **批判性评价** | 基于研究设计的结构化评价 | ✅ |
| 📝 **文献汇总** | 提取关键信息并生成摘要 | ✅ |
| 📚 **系统综述支持** | PRISMA流程辅助 | 🚧 |
| 📈 **Meta分析** | 效应量计算和森林图 | 🚧 |

---

<a name="中文"></a>
## 中文文档

### 🎯 核心功能

#### 1. PubMed文献检索

使用NCBI E-utilities API进行专业医学文献检索，支持完整的PubMed检索语法。

```bash
# 基本检索
python3 scripts/pubmed_search.py "liver cirrhosis AND treatment" 20

# 使用MeSH主题词
python3 scripts/pubmed_search.py '"Liver Cirrhosis"[mh] AND "Drug Therapy"[sh]' 30

# 限定文献类型
python3 scripts/pubmed_search.py '("systematic review"[pt] OR "meta-analysis"[pt]) AND English[la]' 50
```

#### 2. 批判性评价

基于研究设计类型的结构化评价清单：

```bash
# RCT评价清单
python3 scripts/critical_appraisal.py RCT

# 系统综述评价
python3 scripts/critical_appraisal.py systematic_review

# 队列研究评价
python3 scripts/critical_appraisal.py cohort
```

**支持的研究类型：**
- 🎯 **RCT** - 随机对照试验 (Cochrane RoB 2.0)
- 📊 **cohort** - 队列研究 (NOS量表)
- 🔬 **case_control** - 病例对照研究 (NOS量表)
- 📖 **systematic_review** - 系统综述/Meta分析 (AMSTAR 2)
- 📸 **cross_sectional** - 横断面研究 (改良NOS)
- 🔍 **diagnostic** - 诊断试验 (QUADAS-2)

---

### 🚀 快速开始

#### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/erongcao/medlit-research.git
cd medlit-research

# 安装Python依赖
pip3 install requests xml.etree.ElementTree

# 配置NCBI邮箱（必需）
# 编辑 scripts/pubmed_search.py，设置有效邮箱
```

#### 基本使用

**场景1: 检索文献**

```bash
# 检索肝癌治疗的最新文献
python3 scripts/pubmed_search.py "hepatocellular carcinoma AND immunotherapy" 20

# 输出示例
{
  "query": "hepatocellular carcinoma AND immunotherapy",
  "count": 10,
  "results": [
    {
      "pmid": "12345678",
      "title": "Immunotherapy for HCC: current status and future directions",
      "authors": ["Smith J", "Lee K"],
      "journal": "Lancet Oncology",
      "pubdate": "2024 Jan",
      "doi": "10.1016/j.lanonc.2024.01.001",
      "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    }
  ]
}
```

**场景2: 生成评价清单**

```bash
# 生成RCT评价清单
python3 scripts/critical_appraisal.py RCT > appraisal_template.json

# 清单内容
{
  "study_type": "RCT",
  "questions": [
    {
      "id": "randomization",
      "domain": "随机化",
      "question": "随机序列产生是否恰当?",
      "criteria": "使用计算机随机数生成器或随机数字表"
    },
    {
      "id": "allocation_concealment",
      "domain": "分配隐藏",
      "question": "分组分配是否对研究者隐藏?",
      "criteria": "使用中央随机系统或密封不透光信封"
    }
  ]
}
```

**场景3: 完整工作流程**

```bash
# 1. 检索文献
python3 scripts/pubmed_search.py "糖尿病 AND SGLT2抑制剂 AND RCT" 30 > search_results.json

# 2. 下载关键文献
# 根据PMID下载PDF

# 3. 阅读并评价
python3 scripts/critical_appraisal.py RCT > my_appraisal.json

# 4. 填写评价结果
# 使用文本编辑器填写每个问题的答案

# 5. 生成综述
# 汇总多个研究的评价结果
```

---

### 📚 研究类型与评价工具

| 研究类型 | 证据等级 | 评价工具 | 关键评价点 |
|---------|---------|---------|-----------|
| **RCT** | ⭐⭐⭐⭐⭐ | Cochrane RoB 2.0 | 随机化、盲法、失访、选择性报告 |
| **队列研究** | ⭐⭐⭐⭐ | NOS量表 | 暴露定义、混杂控制、随访完整性 |
| **病例对照** | ⭐⭐⭐⭐ | NOS量表 | 病例/对照选择、暴露测量、混杂控制 |
| **系统综述** | ⭐⭐⭐⭐⭐ | AMSTAR 2 | 方案注册、检索策略、偏倚评价、证据分级 |
| **诊断试验** | ⭐⭐⭐⭐ | QUADAS-2 | 病例谱、金标准、流程时间、盲法 |
| **横断面** | ⭐⭐⭐ | 改良NOS | 样本代表性、暴露测量、混杂控制 |

---

### 🔍 检索策略构建

#### PICO框架

```
P (Population)    - 目标人群特征
I (Intervention)  - 干预措施
C (Comparison)    - 对照/比较
O (Outcome)       - 结局指标
```

#### 检索式示例

```bash
# 示例: 二甲双胍治疗2型糖尿病的疗效
"(Metformin[tiab] OR Glucophage[tiab]) AND (Type 2 Diabetes[mh] OR T2DM[tiab]) AND (HbA1c[tiab] OR glycemic control[tiab])"

# 使用过滤器限定高质量证据
"(systematic review[pt] OR meta-analysis[pt] OR randomized controlled trial[pt]) AND English[la] AND 2020:2025[dp]"

# 儿童人群限定
"AND (child[mh] OR pediatric*[tiab] OR paediatric*[tiab] OR infant*[tiab] OR adolescent*[tiab])"
```

#### PubMed检索语法速查

| 语法 | 含义 | 示例 |
|------|------|------|
| `[mh]` | MeSH主题词 | `"Diabetes Mellitus"[mh]` |
| `[tiab]` | 标题/摘要 | `metformin[tiab]` |
| `[pt]` | 文献类型 | `randomized controlled trial[pt]` |
| `[la]` | 语言 | `English[la]` |
| `[dp]` | 发表日期 | `2024:2025[dp]` |
| `AND` | 逻辑与 | `A AND B` |
| `OR` | 逻辑或 | `A OR B` |
| `NOT` | 逻辑非 | `A NOT B` |
| `*` | 截词符 | `diabet*` |
| `""` | 短语检索 | `"type 2 diabetes"` |

---

### 📖 批判性评价流程

#### 第一步: 确定研究类型
阅读文献方法部分，识别研究设计类型。

#### 第二步: 选择评价工具
根据研究类型选择对应的评价清单。

#### 第三步: 逐项评价
- ✅ 低偏倚风险
- ⚠️ 存在一定担忧
- ❌ 高偏倚风险

#### 第四步: 总体判断
```
研究结果是否可信? (内部真实性)
结果是否适用于我的患者? (外部真实性)
获益是否大于风险? (临床适用性)
```

---

### ⚠️ 注意事项

1. **API速率限制**: NCBI建议每秒不超过3次请求
2. **邮箱设置**: 首次使用需在脚本中设置有效邮箱（NCBI要求）
3. **结果解读**: 检索结果是起点，需结合专业知识
4. **伦理使用**: 遵守PubMed使用条款

---

<a name="english"></a>
## English Documentation

### 🎯 Core Features

#### 1. PubMed Literature Search

Professional medical literature search using NCBI E-utilities API with full PubMed syntax support.

```bash
# Basic search
python3 scripts/pubmed_search.py "liver cirrhosis AND treatment" 20

# Using MeSH terms
python3 scripts/pubmed_search.py '"Liver Cirrhosis"[mh] AND "Drug Therapy"[sh]' 30

# Filter by publication type
python3 scripts/pubmed_search.py '("systematic review"[pt] OR "meta-analysis"[pt]) AND English[la]' 50
```

#### 2. Critical Appraisal

Structured appraisal checklists based on study design:

```bash
# Generate RCT appraisal checklist
python3 scripts/critical_appraisal.py RCT

# Systematic review appraisal
python3 scripts/critical_appraisal.py systematic_review

# Cohort study appraisal
python3 scripts/critical_appraisal.py cohort
```

**Supported Study Types:**
- 🎯 **RCT** - Randomized Controlled Trial (Cochrane RoB 2.0)
- 📊 **cohort** - Cohort Study (NOS)
- 🔬 **case_control** - Case-Control Study (NOS)
- 📖 **systematic_review** - Systematic Review/Meta-analysis (AMSTAR 2)
- 📸 **cross_sectional** - Cross-Sectional Study (Modified NOS)
- 🔍 **diagnostic** - Diagnostic Test (QUADAS-2)

---

### 🚀 Quick Start

#### Installation

```bash
# Clone repository
git clone https://github.com/erongcao/medlit-research.git
cd medlit-research

# Install dependencies
pip3 install requests xml.etree.ElementTree

# Configure NCBI email (required)
# Edit scripts/pubmed_search.py and set a valid email
```

#### Basic Usage

**Scenario 1: Literature Search**

```bash
# Search for latest HCC immunotherapy literature
python3 scripts/pubmed_search.py "hepatocellular carcinoma AND immunotherapy" 20
```

**Scenario 2: Generate Appraisal Checklist**

```bash
# Generate RCT appraisal checklist
python3 scripts/critical_appraisal.py RCT > appraisal_template.json
```

**Scenario 3: Complete Workflow**

```bash
# 1. Search literature
python3 scripts/pubmed_search.py "diabetes AND SGLT2 inhibitors AND RCT" 30 > results.json

# 2. Generate appraisal form
python3 scripts/critical_appraisal.py RCT > appraisal.json

# 3. Fill in appraisal results after reading
# Edit appraisal.json with your evaluation
```

---

### 📚 Study Types and Appraisal Tools

| Study Type | Evidence Level | Tool | Key Assessment Points |
|-----------|---------------|------|----------------------|
| **RCT** | ⭐⭐⭐⭐⭐ | Cochrane RoB 2.0 | Randomization, blinding, attrition, selective reporting |
| **Cohort** | ⭐⭐⭐⭐ | NOS | Exposure definition, confounding control, follow-up |
| **Case-Control** | ⭐⭐⭐⭐ | NOS | Case/control selection, exposure measurement, confounding |
| **Systematic Review** | ⭐⭐⭐⭐⭐ | AMSTAR 2 | Protocol registration, search strategy, risk of bias |
| **Diagnostic** | ⭐⭐⭐⭐ | QUADAS-2 | Patient spectrum, reference standard, flow and timing |
| **Cross-Sectional** | ⭐⭐⭐ | Modified NOS | Sample representativeness, exposure measurement |

---

### 🔍 Search Strategy Building

#### PICO Framework

```
P (Population)    - Target population characteristics
I (Intervention)  - Intervention
C (Comparison)    - Control/Comparator
O (Outcome)       - Outcome measures
```

#### Search Syntax Examples

```bash
# Example: Metformin efficacy in type 2 diabetes
"(Metformin[tiab] OR Glucophage[tiab]) AND (Type 2 Diabetes[mh] OR T2DM[tiab]) AND (HbA1c[tiab] OR glycemic control[tiab])"

# High-quality evidence filter
"(systematic review[pt] OR meta-analysis[pt] OR randomized controlled trial[pt]) AND English[la] AND 2020:2025[dp]"
```

---

## 📁 File Structure

```
medlit-research/
├── README.md                    # This file
├── SKILL.md                     # Complete documentation
├── scripts/
│   ├── pubmed_search.py         # PubMed search tool
│   └── critical_appraisal.py    # Critical appraisal generator
└── references/
    ├── appraisal_tools.md       # Appraisal tools reference
    ├── pubmed_syntax.md         # PubMed syntax guide
    └── study_types.md           # Study design reference
```

---

## 🔗 References

### Critical Appraisal Tools

1. **Cochrane RoB 2.0** - Risk of Bias tool for Randomized Trials
   - https://methods.cochrane.org/bias/resources/rob-2-revised-cochrane-risk-bias-tool-randomized-trials

2. **NOS (Newcastle-Ottawa Scale)** - Quality assessment for observational studies
   - https://www.ohri.ca/programs/clinical_epidemiology/oxford.asp

3. **AMSTAR 2** - Appraisal tool for Systematic Reviews
   - https://amstar.ca/Amstar-2.php

4. **QUADAS-2** - Quality Assessment of Diagnostic Accuracy Studies
   - https://www.bris.ac.uk/population-health-sciences/projects/quadas

### PubMed Resources

- PubMed User Guide: https://pubmed.ncbi.nlm.nih.gov/help/
- MeSH Database: https://meshb.nlm.nih.gov/
- NCBI E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25499/

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Roadmap

- [ ] Meta-analysis calculator
- [ ] Forest plot generator
- [ ] PRISMA flow diagram generator
- [ ] Evidence grading (GRADE)
- [ ] Citation management integration

---

## 📝 License

This project is licensed under the MIT License.

---

## 📬 Contact

- GitHub: [@erongcao](https://github.com/erongcao)
- Email: cao_erong@163.com

---

<p align="center">
  <sub>Built with ❤️ for evidence-based medicine</sub>
</p>
