# Medlit-Research Skill 技术档案

**创建日期**: 2025年3月17日  
**最后更新**: 2026年4月10日  
**版本**: v2.2

---

## 1. 概述

Medlit-Research 是一个多数据库医学文献检索工具，支持 PubMed、Embase、Cochrane Library 检索，并提供批判性评价、全文获取、AI辅助分析等功能。

**主要文件位置**:
- 主脚本: `~/.openclaw/workspace/skills/medlit-research/scripts/multi_database_search.py`
- 配置文件: `~/.medlit/config.json`
- 检索历史: `~/.medlit/search_history.json`
- SKILL文档: `~/.openclaw/workspace/skills/medlit-research/SKILL.md`

---

## 2. 核心功能

### 2.1 多数据库检索

| 数据库 | 状态 | 说明 |
|-------|------|------|
| PubMed | ✅ 可用 | 通过 NCBI E-utilities API |
| Embase | ✅ 可用 | 通过 Embase API (api.embase.com) |
| Cochrane | ⚠️ 手动 | 需手动访问或机构订阅 |

### 2.2 改进功能清单

#### ✅ 1. API Key 管理（配置文件支持）
- 支持配置文件存储 API Key 和邮箱
- 配置文件位置: `~/.medlit/config.json`
- 优先读取环境变量，其次配置文件

**使用方法**:
```bash
# 设置 Embase API Key
python3 multi_database_search.py --config embase YOUR_API_KEY

# 设置 NCBI 邮箱（必需）
python3 multi_database_search.py --config email your_email@example.com

# 查看当前配置
python3 multi_database_search.py --config show

# 配置帮助
python3 multi_database_search.py --config help
```

**环境变量方式**:
```bash
export EMBASE_API_KEY='your_key'
export NCBI_EMAIL='your_email@example.com'
```

#### ✅ 3. Embase 作者信息提取完整
- 改进作者提取逻辑，支持多种作者字段格式
- 可提取多位作者（最多5位）
- 支持 `authname`、`given-name` + `surname` 等格式

#### ✅ 4. 去重功能
- 基于 DOI 和标准化标题进行跨数据库去重
- 自动标记文献来源（PubMed only / Embase only / Both）
- 输出去重统计信息

**使用方法**:
```bash
# 默认启用去重（多数据库检索时）
python3 multi_database_search.py "query" --dbs pubmed,embase

# 禁用去重
python3 multi_database_search.py "query" --dbs pubmed,embase --no-dedup
```

#### ✅ 6. 详细错误处理
- 错误分类：`NETWORK_ERROR`、`AUTHENTICATION_ERROR`、`API_RATE_LIMIT`、`TIMEOUT_ERROR` 等
- 提供具体的错误信息和解决建议
- 用户友好的错误提示

#### ✅ 7. 结果导出功能
支持多种导出格式：

| 格式 | 扩展名 | 用途 |
|-----|--------|------|
| CSV | .csv | Excel、数据分析 |
| BibTeX | .bib | LaTeX论文引用 |
| RIS | .ris | EndNote、Zotero |
| JSON | .json | 结构化数据处理 |
| Markdown | .md | 阅读友好的文档 |

**使用方法**:
```bash
# 检索时自动导出
python3 multi_database_search.py "Fanconi syndrome" \
  --dbs pubmed,embase \
  --max 20 \
  --export-format csv \
  --export-path results.csv

# 支持的格式: csv, bibtex, ris, json, md
python3 multi_database_search.py "query" --export-format bibtex

# 从检索历史导出
python3 multi_database_search.py --export <search_id> <format> [output_path]
python3 multi_database_search.py --export b42a5295 bibtex myrefs.bib
```

#### ✅ 8. 检索历史记录
- 自动保存最近50条检索记录
- 包含检索词、数据库、时间范围、结果数
- 每条记录有唯一ID，方便追踪和重新导出

**使用方法**:
```bash
# 查看检索历史
python3 multi_database_search.py --history
python3 multi_database_search.py --history 20  # 显示最近20条
```

---

## 3. 完整使用示例

### 3.1 首次配置
```bash
# 1. 设置 NCBI 邮箱（必需）
python3 multi_database_search.py --config email your_email@example.com

# 2. 设置 Embase API Key（如需要 Embase 检索）
python3 multi_database_search.py --config embase YOUR_API_KEY

# 3. 验证配置
python3 multi_database_search.py --config show
```

### 3.2 基本检索
```bash
# 仅 PubMed
python3 multi_database_search.py "Fanconi syndrome" --max 10

# PubMed + Embase（自动去重）
python3 multi_database_search.py "Fanconi syndrome" \
  --dbs pubmed,embase \
  --max 20 \
  --date 2020:2025

# 导出为 CSV
python3 multi_database_search.py "liver cirrhosis treatment" \
  --dbs pubmed,embase \
  --max 30 \
  --export-format csv \
  --export-path results.csv
```

### 3.3 从历史导出
```bash
# 查看历史
python3 multi_database_search.py --history

# 导出历史记录为不同格式
python3 multi_database_search.py --export b42a5295 bibtex refs.bib
python3 multi_database_search.py --export b42a5295 ris refs.ris
python3 multi_database_search.py --export b42a5295 md refs.md
```

---

## 4. 已知问题与注意事项

### 4.1 API Key 安全
- API Key 存储在 `~/.medlit/config.json`（明文存储）
- 建议设置文件权限：`chmod 600 ~/.medlit/config.json`
- 优先使用环境变量（更安全）

### 4.2 NCBI 邮箱要求
- NCBI 要求提供真实邮箱
- 未配置邮箱时会显示警告，但仍可使用默认邮箱运行

### 4.3 Embase API 限制
- 通过 Embase API (api.embase.com/v2/search) 访问
- 需要有效的 Embase API Key
- 有速率限制（建议每秒不超过3次请求）

### 4.4 Cochrane Library
- 目前仅支持生成搜索 URL
- 需要手动访问或机构订阅才能获取全文

---

## 5. 故障排除

### 问题1: Embase 返回 401/403 错误
**原因**: API Key 未配置或无效  
**解决**:
```bash
python3 multi_database_search.py --config embase YOUR_API_KEY
```

### 问题2: NCBI 邮箱警告
**原因**: 未配置 NCBI 邮箱  
**解决**:
```bash
python3 multi_database_search.py --config email your_email@example.com
```

### 问题3: 网络超时
**原因**: 网络连接问题或 API 响应慢  
**解决**: 检查网络连接，稍后重试

### 问题4: 检索结果为空
**原因**: 检索词太具体或时间范围限制  
**解决**: 放宽检索条件，扩大时间范围

---

## 6. 更新日志

### v2.2 (2026-04-10)
- ✅ Embase 检索改为正确的 Embase API 端点
- ✅ AI 分析集成 mmx (MiniMax)
- ✅ 删除重复/废弃脚本
- ✅ TECHNICAL_DOCUMENTATION.md 与代码同步

### v2.0 (2025-03-17)
- ✅ 新增配置文件管理（API Key 和邮箱）
- ✅ 改进 Embase 作者提取（支持多位作者）
- ✅ 新增跨数据库去重功能
- ✅ 新增详细错误处理和分类
- ✅ 新增结果导出功能（CSV/BibTeX/RIS/JSON/Markdown）
- ✅ 新增检索历史记录

---

## 7. 相关文件

| 文件 | 路径 | 说明 |
|-----|------|------|
| 主脚本 | `scripts/multi_database_search.py` | 多数据库检索主程序 |
| 全文获取 | `scripts/pmc_fulltext.py` | PMC 全文下载 |
| 全文评价 | `scripts/fulltext_appraisal.py` | 评价清单模板生成 |
| AI 分析 | `scripts/ai_assistant.py` | AI 辅助分析（mmx/MiniMax） |
| SKILL 文档 | `SKILL.md` | 完整使用文档 |
| 配置文件 | `~/.medlit/config.json` | API Key 和邮箱 |
| 检索历史 | `~/.medlit/search_history.json` | 检索记录 |

---

## 8. 联系与支持

如有问题或建议，请检查：
1. 本技术档案
2. SKILL.md 文档
3. 脚本内置帮助：`python3 multi_database_search.py --help`

---

**文档维护**: 定期更新，记录新功能和修复  
**下次更新提醒**: 添加新数据库支持、改进 Cochrane 检索
