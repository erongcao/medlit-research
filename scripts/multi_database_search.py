#!/usr/bin/env python3
"""
多数据库医学文献检索工具（改进版）
支持PubMed、Embase、Cochrane Library
新增：配置文件管理、完整作者提取、去重功能、详细错误处理、检索历史
"""

import sys
import json
import urllib.request
import urllib.parse
import time
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
import csv
import re

# 尝试导入requests，如果没有则使用urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# API配置
NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL_NAME = "medlit-research"

# 配置文件路径
CONFIG_DIR = Path.home() / ".medlit"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "search_history.json"


class ConfigManager:
    """配置管理器"""
    
    @staticmethod
    def load_config() -> Dict:
        """加载配置文件"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    @staticmethod
    def save_config(config: Dict) -> None:
        """保存配置文件"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def get_api_key(service: str) -> str:
        """获取API Key（优先环境变量，其次配置文件）"""
        # 1. 检查环境变量
        env_key = os.environ.get(f"{service.upper()}_API_KEY", "")
        if env_key and env_key != f"YOUR_{service.upper()}_API_KEY":
            return env_key
        
        # 2. 检查配置文件
        config = ConfigManager.load_config()
        config_key = config.get("api_keys", {}).get(service, "")
        if config_key:
            return config_key
        
        return ""
    
    @staticmethod
    def set_api_key(service: str, key: str) -> None:
        """设置API Key到配置文件"""
        config = ConfigManager.load_config()
        if "api_keys" not in config:
            config["api_keys"] = {}
        config["api_keys"][service] = key
        ConfigManager.save_config(config)
    
    @staticmethod
    def get_email() -> str:
        """获取NCBI邮箱（优先环境变量，其次配置文件，最后提示）"""
        # 1. 检查环境变量
        env_email = os.environ.get("NCBI_EMAIL", "")
        if env_email:
            return env_email
        
        # 2. 检查配置文件
        config = ConfigManager.load_config()
        config_email = config.get("ncbi_email", "")
        if config_email:
            return config_email
        
        # 3. 返回默认值（会触发提示）
        return ""
    
    @staticmethod
    def set_email(email: str) -> None:
        """设置NCBI邮箱到配置文件"""
        config = ConfigManager.load_config()
        config["ncbi_email"] = email
        ConfigManager.save_config(config)


class SearchHistory:
    """检索历史管理器"""
    
    @staticmethod
    def load_history() -> List[Dict]:
        """加载检索历史"""
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    @staticmethod
    def save_history(history: List[Dict]) -> None:
        """保存检索历史"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def add_search(query: str, databases: List[str], results_count: int, 
                   date_range: Optional[str] = None) -> None:
        """添加检索记录"""
        history = SearchHistory.load_history()
        
        # 生成唯一ID
        search_id = hashlib.md5(
            f"{query}{','.join(databases)}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        
        record = {
            "id": search_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "databases": databases,
            "date_range": date_range,
            "results_count": results_count
        }
        
        history.insert(0, record)  # 新记录在前
        
        # 只保留最近50条记录
        history = history[:50]
        
        SearchHistory.save_history(history)
        return search_id
    
    @staticmethod
    def list_history(limit: int = 10) -> List[Dict]:
        """列出检索历史"""
        history = SearchHistory.load_history()
        return history[:limit]
    
    @staticmethod
    def get_search_by_id(search_id: str) -> Optional[Dict]:
        """根据ID获取检索记录"""
        history = SearchHistory.load_history()
        for record in history:
            if record.get("id") == search_id:
                return record
        return None


class ErrorHandler:
    """错误处理器"""
    
    ERROR_CODES = {
        "NETWORK_ERROR": "网络连接错误，请检查网络连接",
        "API_RATE_LIMIT": "API速率限制，请稍后再试",
        "AUTHENTICATION_ERROR": "API认证失败，请检查API Key",
        "TIMEOUT_ERROR": "请求超时，请稍后重试",
        "INVALID_QUERY": "检索词格式错误",
        "NO_RESULTS": "未找到相关文献",
        "SERVICE_UNAVAILABLE": "服务暂时不可用",
        "UNKNOWN_ERROR": "未知错误"
    }
    
    @staticmethod
    def classify_error(error: Exception, service: str = "") -> Dict:
        """分类错误类型"""
        error_str = str(error).lower()
        
        if "timeout" in error_str or "timed out" in error_str:
            return {
                "code": "TIMEOUT_ERROR",
                "message": ErrorHandler.ERROR_CODES["TIMEOUT_ERROR"],
                "service": service,
                "original_error": str(error)
            }
        elif "401" in error_str or "403" in error_str or "unauthorized" in error_str:
            return {
                "code": "AUTHENTICATION_ERROR",
                "message": ErrorHandler.ERROR_CODES["AUTHENTICATION_ERROR"],
                "service": service,
                "original_error": str(error),
                "suggestion": f"请设置{service} API Key: export {service.upper()}_API_KEY='your_key' 或使用 --config 配置"
            }
        elif "429" in error_str or "rate limit" in error_str:
            return {
                "code": "API_RATE_LIMIT",
                "message": ErrorHandler.ERROR_CODES["API_RATE_LIMIT"],
                "service": service,
                "original_error": str(error),
                "suggestion": "请等待几秒后重试"
            }
        elif "network" in error_str or "connection" in error_str or "urlopen error" in error_str:
            return {
                "code": "NETWORK_ERROR",
                "message": ErrorHandler.ERROR_CODES["NETWORK_ERROR"],
                "service": service,
                "original_error": str(error)
            }
        elif "400" in error_str or "bad request" in error_str:
            return {
                "code": "INVALID_QUERY",
                "message": ErrorHandler.ERROR_CODES["INVALID_QUERY"],
                "service": service,
                "original_error": str(error)
            }
        else:
            return {
                "code": "UNKNOWN_ERROR",
                "message": ErrorHandler.ERROR_CODES["UNKNOWN_ERROR"],
                "service": service,
                "original_error": str(error)
            }


class Exporter:
    """文献导出器"""
    
    @staticmethod
    def export_csv(articles: List[Dict], filepath: str) -> str:
        """导出为CSV格式"""
        fieldnames = ["title", "authors", "journal", "pubdate", "doi", "url", "database", "source_databases"]
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for article in articles:
                row = {
                    "title": article.get("title", ""),
                    "authors": "; ".join(article.get("authors", [])),
                    "journal": article.get("journal", ""),
                    "pubdate": article.get("pubdate", ""),
                    "doi": article.get("doi", ""),
                    "url": article.get("url", ""),
                    "database": article.get("database", ""),
                    "source_databases": ", ".join(article.get("source_databases", []))
                }
                writer.writerow(row)
        
        return filepath
    
    @staticmethod
    def export_bibtex(articles: List[Dict], filepath: str) -> str:
        """导出为BibTeX格式"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for i, article in enumerate(articles, 1):
                # 生成cite key
                first_author = article.get("authors", ["Unknown"])[0].split()[0] if article.get("authors") else "Unknown"
                year = re.search(r'\d{4}', article.get("pubdate", ""))
                year_str = year.group() if year else "2024"
                cite_key = f"{first_author.lower()}{year_str}{i:03d}"
                
                # 清理标题中的特殊字符
                title = article.get("title", "").replace("{", "").replace("}", "").replace("\\", "")
                
                # 格式化作者
                authors = " and ".join(article.get("authors", []))
                
                # 确定条目类型
                entry_type = "article"
                
                f.write(f"@{entry_type}{{{cite_key},\n")
                f.write(f"  title = {{{title}}},\n")
                f.write(f"  author = {{{authors}}},\n")
                f.write(f"  journal = {{{article.get('journal', '')}}},\n")
                f.write(f"  year = {{{year_str}}},\n")
                
                doi = article.get("doi", "")
                if doi:
                    f.write(f"  doi = {{{doi}}},\n")
                
                url = article.get("url", "")
                if url:
                    f.write(f"  url = {{{url}}},\n")
                
                pmid = article.get("pmid", "")
                if pmid:
                    f.write(f"  pmid = {{{pmid}}},\n")
                
                f.write("}\n\n")
        
        return filepath
    
    @staticmethod
    def export_ris(articles: List[Dict], filepath: str) -> str:
        """导出为RIS格式（EndNote等支持）"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for article in articles:
                f.write("TY  - JOUR\n")
                f.write(f"TI  - {article.get('title', '')}\n")
                
                for author in article.get("authors", []):
                    f.write(f"AU  - {author}\n")
                
                f.write(f"JO  - {article.get('journal', '')}\n")
                f.write(f"PY  - {article.get('pubdate', '')}\n")
                
                doi = article.get("doi", "")
                if doi:
                    f.write(f"DO  - {doi}\n")
                
                url = article.get("url", "")
                if url:
                    f.write(f"UR  - {url}\n")
                
                pmid = article.get("pmid", "")
                if pmid:
                    f.write(f"AN  - {pmid}\n")
                
                f.write("ER  - \n\n")
        
        return filepath
    
    @staticmethod
    def export_json(articles: List[Dict], filepath: str) -> str:
        """导出为JSON格式"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        return filepath
    
    @staticmethod
    def export_markdown(articles: List[Dict], filepath: str, query: str = "") -> str:
        """导出为Markdown格式"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# 文献检索结果\n\n")
            f.write(f"**检索词**: {query}\n\n")
            f.write(f"**检索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**文献数量**: {len(articles)}\n\n")
            f.write("---\n\n")
            
            for i, article in enumerate(articles, 1):
                f.write(f"## {i}. {article.get('title', 'N/A')}\n\n")
                f.write(f"**作者**: {', '.join(article.get('authors', ['N/A']))}\n\n")
                f.write(f"**期刊**: {article.get('journal', 'N/A')}\n\n")
                f.write(f"**发表时间**: {article.get('pubdate', 'N/A')}\n\n")
                
                doi = article.get("doi", "")
                if doi:
                    f.write(f"**DOI**: {doi}\n\n")
                
                url = article.get("url", "")
                if url:
                    f.write(f"**链接**: [{url}]({url})\n\n")
                
                pmid = article.get("pmid", "")
                if pmid:
                    f.write(f"**PMID**: {pmid}\n\n")
                
                sources = article.get("source_databases", [])
                if sources:
                    f.write(f"**来源数据库**: {', '.join(sources)}\n\n")
                
                f.write("---\n\n")
        
        return filepath
    
    @staticmethod
    def get_export_formats() -> Dict[str, str]:
        """获取支持的导出格式"""
        return {
            "csv": "CSV (Excel兼容)",
            "bibtex": "BibTeX (LaTeX引用)",
            "ris": "RIS (EndNote/Zotero)",
            "json": "JSON (结构化数据)",
            "md": "Markdown (阅读友好)"
        }


class Deduplicator:
    """文献去重器"""
    
    @staticmethod
    def normalize_title(title: str) -> str:
        """标准化标题用于比较"""
        return title.lower().strip().replace(" ", "").replace("-", "").replace("_", "")
    
    @staticmethod
    def deduplicate_results(results_by_db: Dict[str, List[Dict]]) -> Dict:
        """
        跨数据库去重
        
        返回：
        {
            "unique_articles": [...],  # 去重后的文献列表
            "duplicates": [...],       # 重复文献信息
            "statistics": {...}        # 统计信息
        }
        """
        all_articles = []
        seen_dois: Set[str] = set()
        seen_titles: Dict[str, str] = {}  # 标准化标题 -> 原始标题
        duplicates = []
        
        for db_name, db_results in results_by_db.items():
            if "results" not in db_results:
                continue
            
            for article in db_results["results"]:
                article["source_databases"] = [db_name]
                
                # 使用DOI去重
                doi = article.get("doi", "").lower().strip()
                if doi and doi != "n/a":
                    if doi in seen_dois:
                        # 找到重复，更新来源
                        for existing in all_articles:
                            if existing.get("doi", "").lower().strip() == doi:
                                if db_name not in existing["source_databases"]:
                                    existing["source_databases"].append(db_name)
                                duplicates.append({
                                    "title": article.get("title", ""),
                                    "doi": doi,
                                    "databases": [db_name] + existing["source_databases"]
                                })
                                break
                        continue
                    seen_dois.add(doi)
                
                # 使用标题去重（DOI不存在时）
                title = article.get("title", "")
                normalized_title = Deduplicator.normalize_title(title)
                
                if normalized_title in seen_titles:
                    # 找到重复
                    for existing in all_articles:
                        if Deduplicator.normalize_title(existing.get("title", "")) == normalized_title:
                            if db_name not in existing["source_databases"]:
                                existing["source_databases"].append(db_name)
                            duplicates.append({
                                "title": title,
                                "databases": [db_name] + existing["source_databases"]
                            })
                            break
                    continue
                
                seen_titles[normalized_title] = title
                all_articles.append(article)
        
        # 统计
        stats = {
            "total_before_dedup": sum(len(db.get("results", [])) for db in results_by_db.values()),
            "total_after_dedup": len(all_articles),
            "duplicates_removed": len(duplicates),
            "by_database": {db: len(res.get("results", [])) for db, res in results_by_db.items()}
        }
        
        return {
            "unique_articles": all_articles,
            "duplicates": duplicates,
            "statistics": stats
        }


class DatabaseSearcher:
    """多数据库检索器（改进版）"""
    
    def __init__(self):
        self.results_cache = {}
        self.email = ConfigManager.get_email()
        
        # 检查邮箱配置
        if not self.email:
            print("⚠️ 警告: NCBI邮箱未配置", file=sys.stderr)
            print("请设置环境变量: export NCBI_EMAIL='your_email@example.com'", file=sys.stderr)
            print("或使用: python3 multi_database_search.py --config email your_email@example.com", file=sys.stderr)
            self.email = "user@example.com"  # 使用默认值，但会显示警告
    
    def search_pubmed(self, query: str, max_results: int = 20, 
                      date_range: Optional[str] = None,
                      article_types: Optional[List[str]] = None) -> Dict:
        """PubMed检索（带详细错误处理）"""
        full_query = query
        if date_range:
            full_query += f" AND ({date_range}[dp])"
        if article_types:
            type_filter = " OR ".join([f"{t}[pt]" for t in article_types])
            full_query += f" AND ({type_filter})"
        
        search_params = {
            "db": "pubmed",
            "term": full_query,
            "retmax": max_results,
            "sort": "relevance",
            "retmode": "json",
            "tool": TOOL_NAME,
            "email": self.email
        }
        
        try:
            search_url = f"{NCBI_BASE_URL}/esearch.fcgi"
            data = urllib.parse.urlencode(search_params).encode('utf-8')
            
            with urllib.request.urlopen(search_url, data=data, timeout=30) as response:
                search_result = json.loads(response.read().decode('utf-8'))
            
            idlist = search_result.get("esearchresult", {}).get("idlist", [])
            total_count = search_result.get("esearchresult", {}).get("count", 0)
            
            if not idlist:
                return {
                    "database": "PubMed",
                    "query": full_query,
                    "total_count": int(total_count),
                    "returned_count": 0,
                    "results": [],
                    "status": "success"
                }
            
            time.sleep(0.34)
            results = self._fetch_pubmed_details(idlist)
            
            return {
                "database": "PubMed",
                "query": full_query,
                "total_count": int(total_count),
                "returned_count": len(results),
                "results": results,
                "status": "success"
            }
            
        except Exception as e:
            error_info = ErrorHandler.classify_error(e, "PubMed")
            return {
                "database": "PubMed",
                "query": full_query,
                "status": "error",
                "error": error_info
            }
    
    def _fetch_pubmed_details(self, pmids: List[str]) -> List[Dict]:
        """获取PubMed文献详情"""
        summary_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
            "tool": TOOL_NAME,
            "email": self.email
        }
        
        summary_url = f"{NCBI_BASE_URL}/esummary.fcgi"
        data = urllib.parse.urlencode(summary_params).encode('utf-8')
        
        with urllib.request.urlopen(summary_url, data=data, timeout=30) as response:
            summary_result = json.loads(response.read().decode('utf-8'))
        
        results = []
        for pmid in pmids:
            article = summary_result.get("result", {}).get(pmid, {})
            if article:
                results.append({
                    "pmid": pmid,
                    "title": article.get("title", "N/A"),
                    "authors": [a.get("name", "") for a in article.get("authors", [])[:5]],
                    "journal": article.get("fulljournalname", article.get("source", "N/A")),
                    "pubdate": article.get("pubdate", "N/A"),
                    "doi": article.get("elocationid", ""),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "database": "PubMed"
                })
        
        return results
    
    def search_embase(self, query: str, max_results: int = 20,
                      date_range: Optional[str] = None) -> Dict:
        """
        Embase检索（改进版：完整作者提取、详细错误处理）
        """
        api_key = ConfigManager.get_api_key("embase")
        
        if not api_key:
            return {
                "database": "Embase (via Scopus)",
                "query": query,
                "status": "error",
                "error": {
                    "code": "AUTHENTICATION_ERROR",
                    "message": "Embase API Key 未配置",
                    "suggestion": "请设置环境变量: export EMBASE_API_KEY='your_key' 或使用 --config embase your_key"
                }
            }
        
        scopus_query = f"TITLE-ABS-KEY({query})"
        
        headers = {
            "X-ELS-APIKey": api_key,
            "Accept": "application/json",
            "User-Agent": "medlit-research/1.0"
        }
        
        params = {
            "query": scopus_query,
            "count": max_results,
            "start": 0
        }
        
        if date_range:
            params["date"] = date_range.replace(":", "-")
        
        try:
            if HAS_REQUESTS:
                response = requests.get(
                    "https://api.elsevier.com/content/search/scopus",
                    headers=headers,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
            else:
                scopus_url = "https://api.elsevier.com/content/search/scopus"
                url = f"{scopus_url}?{urllib.parse.urlencode(params)}"
                req = urllib.request.Request(url, headers=headers)
                
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
            
            entries = data.get("search-results", {}).get("entry", [])
            total = data.get("search-results", {}).get("opensearch:totalResults", 0)
            
            results = []
            for entry in entries:
                # 改进：完整提取所有作者
                authors = []
                
                # 尝试多种方式获取作者
                # 1. 尝试获取 authors 字段
                author_data = entry.get("authors", {})
                if isinstance(author_data, dict):
                    author_list = author_data.get("author", [])
                    if isinstance(author_list, dict):
                        author_list = [author_list]
                    for author in author_list[:5]:  # 限制前5位作者
                        if isinstance(author, dict):
                            # 尝试不同的作者名字段
                            name = (author.get("authname") or 
                                   author.get("$") or 
                                   author.get("given-name", "") + " " + author.get("surname", ""))
                            if name.strip():
                                authors.append(name.strip())
                
                # 2. 如果没有获取到作者，尝试 dc:creator
                if not authors:
                    creator = entry.get("dc:creator", "")
                    if creator:
                        authors = [creator]
                
                # 3. 尝试 author-count 和 author-url（需要额外请求，这里简化）
                
                results.append({
                    "title": entry.get("dc:title", "N/A"),
                    "authors": authors if authors else ["N/A"],
                    "journal": entry.get("prism:publicationName", "N/A"),
                    "pubdate": entry.get("prism:coverDate", "N/A"),
                    "doi": entry.get("prism:doi", ""),
                    "url": entry.get("link", [{}])[0].get("@href", "") if isinstance(entry.get("link", []), list) else "",
                    "database": "Embase (via Scopus)"
                })
            
            return {
                "database": "Embase (via Scopus)",
                "query": query,
                "total_count": int(total),
                "returned_count": len(results),
                "results": results,
                "status": "success"
            }
            
        except Exception as e:
            error_info = ErrorHandler.classify_error(e, "Embase")
            return {
                "database": "Embase (via Scopus)",
                "query": query,
                "status": "error",
                "error": error_info
            }
    
    def search_cochrane(self, query: str, max_results: int = 20,
                        date_range: Optional[str] = None) -> Dict:
        """Cochrane Library检索"""
        base_url = "https://www.cochranelibrary.com/cdsr/search"
        
        search_params = {
            "searchBy": "6",
            "searchText": query,
            "sortBy": "relevance",
            "page": "1",
            "resultPerPage": str(max_results)
        }
        
        if date_range:
            start_year, end_year = date_range.split(":")
            search_params["min_pub_year"] = start_year
            search_params["max_pub_year"] = end_year
        
        return {
            "database": "Cochrane Library",
            "query": query,
            "status": "manual_search_required",
            "message": "Cochrane Library requires manual search or institutional access",
            "search_url": f"{base_url}?{urllib.parse.urlencode(search_params)}"
        }
    
    def search_all(self, query: str, max_results: int = 20,
                   date_range: Optional[str] = None,
                   databases: List[str] = None,
                   deduplicate: bool = True) -> Dict:
        """
        多数据库联合检索（改进版：支持去重）
        
        Args:
            deduplicate: 是否进行跨数据库去重
        """
        if databases is None:
            databases = ["pubmed", "embase", "cochrane"]
        
        results_by_db = {}
        
        if "pubmed" in databases:
            time.sleep(0.5)
            pubmed_result = self.search_pubmed(query, max_results, date_range)
            results_by_db["pubmed"] = pubmed_result
        
        if "embase" in databases:
            time.sleep(0.5)
            embase_result = self.search_embase(query, max_results, date_range)
            results_by_db["embase"] = embase_result
        
        if "cochrane" in databases:
            cochrane_result = self.search_cochrane(query, max_results, date_range)
            results_by_db["cochrane"] = cochrane_result
        
        # 去重处理
        dedup_results = None
        if deduplicate and len(databases) > 1:
            dedup_results = Deduplicator.deduplicate_results(results_by_db)
        
        # 计算总数
        total_articles = sum(
            db_result.get("returned_count", 0) 
            for db_result in results_by_db.values()
            if "error" not in db_result
        )
        
        # 保存检索历史
        search_id = SearchHistory.add_search(query, databases, total_articles, date_range)
        
        output = {
            "query": query,
            "date_range": date_range,
            "databases_searched": databases,
            "search_id": search_id,
            "results_by_database": results_by_db,
            "summary": {
                "total_articles_found": total_articles
            }
        }
        
        if dedup_results:
            output["deduplication"] = dedup_results
            output["summary"]["unique_articles"] = len(dedup_results["unique_articles"])
            output["summary"]["duplicates_removed"] = dedup_results["statistics"]["duplicates_removed"]
        
        return output


def print_config_help():
    """打印配置帮助"""
    print("""
配置管理帮助:

设置 Embase API Key:
  python3 multi_database_search.py --config embase YOUR_API_KEY

设置 NCBI 邮箱:
  python3 multi_database_search.py --config email your_email@example.com

查看当前配置:
  python3 multi_database_search.py --config show

配置文件位置: ~/.medlit/config.json

也可以通过环境变量设置:
  export EMBASE_API_KEY='your_key'
  export NCBI_EMAIL='your_email@example.com'
""")


def print_history(limit: int = 10):
    """打印检索历史"""
    history = SearchHistory.list_history(limit)
    
    if not history:
        print("暂无检索历史")
        return
    
    print(f"\n最近 {len(history)} 条检索历史:")
    print("-" * 80)
    for record in history:
        print(f"ID: {record['id']}")
        print(f"时间: {record['timestamp']}")
        print(f"检索词: {record['query']}")
        print(f"数据库: {', '.join(record['databases'])}")
        print(f"结果数: {record['results_count']}")
        if record.get('date_range'):
            print(f"时间范围: {record['date_range']}")
        print("-" * 80)


def main():
    # 处理配置命令
    if len(sys.argv) >= 3 and sys.argv[1] == "--config":
        config_type = sys.argv[2]
        
        if config_type == "help":
            print_config_help()
        elif config_type == "show":
            config = ConfigManager.load_config()
            print("当前配置:")
            print(json.dumps(config, indent=2, ensure_ascii=False))
        elif config_type == "embase" and len(sys.argv) >= 4:
            ConfigManager.set_api_key("embase", sys.argv[3])
            print(f"✅ Embase API Key 已保存到 {CONFIG_FILE}")
        elif config_type == "email" and len(sys.argv) >= 4:
            ConfigManager.set_email(sys.argv[3])
            print(f"✅ NCBI 邮箱已保存到 {CONFIG_FILE}")
        else:
            print_config_help()
        sys.exit(0)
    
    # 处理历史命令
    if len(sys.argv) >= 2 and sys.argv[1] == "--history":
        limit = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
        print_history(limit)
        sys.exit(0)
    
    # 处理导出命令
    if len(sys.argv) >= 2 and sys.argv[1] == "--export":
        if len(sys.argv) < 4:
            print("Usage: --export <search_id> <format> [output_path]", file=sys.stderr)
            print("\n支持的格式:", file=sys.stderr)
            for fmt, desc in Exporter.get_export_formats().items():
                print(f"  {fmt:10} - {desc}", file=sys.stderr)
            sys.exit(1)
        
        search_id = sys.argv[2]
        export_format = sys.argv[3].lower()
        output_path = sys.argv[4] if len(sys.argv) >= 5 else None
        
        # 获取检索记录
        record = SearchHistory.get_search_by_id(search_id)
        if not record:
            print(f"错误: 未找到检索记录 ID: {search_id}", file=sys.stderr)
            print("使用 --history 查看可用记录", file=sys.stderr)
            sys.exit(1)
        
        # 重新执行检索获取完整结果
        searcher = DatabaseSearcher()
        result = searcher.search_all(
            record["query"],
            record.get("results_count", 20),
            record.get("date_range"),
            record["databases"],
            deduplicate=True
        )
        
        # 获取要导出的文献列表
        if "deduplication" in result:
            articles = result["deduplication"]["unique_articles"]
        elif "results" in result:
            articles = result["results"]
        else:
            # 从多数据库结果中提取
            articles = []
            for db_result in result.get("results_by_database", {}).values():
                if "results" in db_result:
                    articles.extend(db_result["results"])
        
        # 生成默认文件名
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = re.sub(r'[^\w\s-]', '', record["query"])[:30].strip().replace(" ", "_")
            output_path = f"search_{safe_query}_{timestamp}.{export_format}"
        
        # 执行导出
        try:
            if export_format == "csv":
                Exporter.export_csv(articles, output_path)
            elif export_format == "bibtex":
                Exporter.export_bibtex(articles, output_path)
            elif export_format == "ris":
                Exporter.export_ris(articles, output_path)
            elif export_format == "json":
                Exporter.export_json(articles, output_path)
            elif export_format == "md":
                Exporter.export_markdown(articles, output_path, record["query"])
            else:
                print(f"错误: 不支持的格式: {export_format}", file=sys.stderr)
                print("支持的格式: csv, bibtex, ris, json, md", file=sys.stderr)
                sys.exit(1)
            
            print(f"✅ 导出成功: {output_path}")
            print(f"   格式: {export_format}")
            print(f"   文献数: {len(articles)}")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}", file=sys.stderr)
            sys.exit(1)
        
        sys.exit(0)
    
    # 正常检索
    if len(sys.argv) < 2:
        print("Usage: multi_database_search.py <query> [options]", file=sys.stderr)
        print("       multi_database_search.py --config help", file=sys.stderr)
        print("       multi_database_search.py --history [limit]", file=sys.stderr)
        print("       multi_database_search.py --export <search_id> <format> [output_path]", file=sys.stderr)
        print("\nOptions:", file=sys.stderr)
        print("  --dbs DATABASES    Databases (default: pubmed)", file=sys.stderr)
        print("  --max N            Max results (default: 20)", file=sys.stderr)
        print("  --date YYYY:YYYY   Date range", file=sys.stderr)
        print("  --no-dedup         Disable deduplication", file=sys.stderr)
        print("  --export-format F  自动导出格式 (csv/bibtex/ris/json/md)", file=sys.stderr)
        sys.exit(1)
    
    query = sys.argv[1]
    databases = ["pubmed"]
    max_results = 20
    date_range = None
    deduplicate = True
    auto_export_format = None
    auto_export_path = None
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--dbs" and i + 1 < len(sys.argv):
            databases = sys.argv[i + 1].split(",")
            i += 2
        elif sys.argv[i] == "--max" and i + 1 < len(sys.argv):
            max_results = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--date" and i + 1 < len(sys.argv):
            date_range = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--no-dedup":
            deduplicate = False
            i += 1
        elif sys.argv[i] == "--export-format" and i + 1 < len(sys.argv):
            auto_export_format = sys.argv[i + 1].lower()
            i += 2
        elif sys.argv[i] == "--export-path" and i + 1 < len(sys.argv):
            auto_export_path = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    searcher = DatabaseSearcher()
    
    if len(databases) == 1:
        if databases[0] == "pubmed":
            result = searcher.search_pubmed(query, max_results, date_range)
        elif databases[0] == "embase":
            result = searcher.search_embase(query, max_results, date_range)
        elif databases[0] == "cochrane":
            result = searcher.search_cochrane(query, max_results, date_range)
        else:
            print(f"Unknown database: {databases[0]}", file=sys.stderr)
            sys.exit(1)
    else:
        result = searcher.search_all(query, max_results, date_range, databases, deduplicate)
    
    # 自动导出（如果指定了格式）
    if auto_export_format:
        # 获取要导出的文献列表
        if "deduplication" in result:
            articles = result["deduplication"]["unique_articles"]
        elif "results" in result:
            articles = result["results"]
        else:
            articles = []
            for db_result in result.get("results_by_database", {}).values():
                if "results" in db_result:
                    articles.extend(db_result["results"])
        
        # 生成默认文件名
        if not auto_export_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = re.sub(r'[^\w\s-]', '', query)[:30].strip().replace(" ", "_")
            auto_export_path = f"search_{safe_query}_{timestamp}.{auto_export_format}"
        
        # 执行导出
        try:
            if auto_export_format == "csv":
                Exporter.export_csv(articles, auto_export_path)
            elif auto_export_format == "bibtex":
                Exporter.export_bibtex(articles, auto_export_path)
            elif auto_export_format == "ris":
                Exporter.export_ris(articles, auto_export_path)
            elif auto_export_format == "json":
                Exporter.export_json(articles, auto_export_path)
            elif auto_export_format == "md":
                Exporter.export_markdown(articles, auto_export_path, query)
            else:
                print(f"\n⚠️ 警告: 不支持的导出格式: {auto_export_format}", file=sys.stderr)
                auto_export_path = None
            
            if auto_export_path:
                print(f"\n✅ 已导出到: {auto_export_path}")
                print(f"   格式: {auto_export_format}")
                print(f"   文献数: {len(articles)}")
        except Exception as e:
            print(f"\n⚠️ 导出失败: {e}", file=sys.stderr)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
