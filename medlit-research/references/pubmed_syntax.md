# PubMed 检索语法参考

## 基本检索

| 运算符 | 功能 | 示例 |
|--------|------|------|
| `AND` | 同时包含所有词 | `cancer AND therapy` |
| `OR` | 包含任一词语 | `tumor OR neoplasm` |
| `NOT` | 排除词语 | `cancer NOT breast` |
| `""` | 精确短语 | `"systematic review"` |
| `*` | 截词符 | `cancer*` (cancer, cancers, cancerous) |
| `?` | 单字符通配符 | `wom?n` (woman, women) |

## 字段限定

| 字段 | 说明 | 示例 |
|------|------|------|
| `[ti]` | 标题 | `aspirin[ti]` |
| `[tiab]` | 标题/摘要 | `aspirin[tiab]` |
| `[au]` | 作者 | `Smith[au]` |
| `[ad]` | 作者单位 | `Harvard[ad]` |
| `[dp]` | 发表日期 | `2023:2024[dp]` |
| `[ta]` | 期刊名 | `NEJM[ta]` |
| `[la]` | 语言 | `English[la]` |
| `[pt]` | 文献类型 | `Clinical Trial[pt]` |
| `[mh]` | MeSH主题词 | `Liver Neoplasms[mh]` |
| `[sh]` | MeSH副主题词 | `therapeutic use[sh]` |

## 文献类型过滤器

```
Clinical Trial[pt]
Randomized Controlled Trial[pt]
Meta-Analysis[pt]
Systematic Review[pt]
Review[pt]
Practice Guideline[pt]
Observational Study[pt]
Case Reports[pt]
```

## PICO检索示例

**问题**: 二甲双胍治疗2型糖尿病患者的心血管结局

```
P (Population): type 2 diabetes[mh] OR type 2 diabet*[tiab]
I (Intervention): metformin[mh] OR metformin[tiab]
C (Comparison): placebo OR standard care
O (Outcome): cardiovascular[tiab] OR myocardial infarction[mh]

组合: ("type 2 diabetes"[mh] OR "type 2 diabet*"[tiab]) AND (metformin[mh] OR metformin[tiab]) AND (cardiovascular[tiab] OR "myocardial infarction"[mh])
```

## 常用检索策略

### 系统综述过滤器
```
systematic review[pt] OR meta-analysis[pt] OR ("systematic review"[ti] AND review[pt])
```

### RCT过滤器
```
randomized controlled trial[pt] OR randomised controlled trial[pt] OR (randomized[tiab] AND controlled[tiab] AND trial[tiab])
```

### 人类研究过滤器
```
Humans[mh] OR human[ti] NOT Animals[mh]
```

### 英文文献过滤器
```
English[la]
```

### 近5年文献
```
(2020:2025[dp])
```

## 高级检索示例

**检索某作者的系统综述**
```
Smith[au] AND (systematic review[pt] OR meta-analysis[pt])
```

**检索特定期刊的指南**
```
NEJM[ta] AND Practice Guideline[pt] AND 2023:2024[dp]
```

**检索某疾病的临床试验**
```
"liver cirrhosis"[mh] AND Randomized Controlled Trial[pt] AND Humans[mh] AND English[la]
```

## MeSH主题词建议

- 使用PubMed MeSH数据库查找准确的主题词
- 主题词会自动包含下位词
- 可同时使用主题词和自由词检索以提高查全率
- 使用 `[mh:noexp]` 限制不扩展下位词
