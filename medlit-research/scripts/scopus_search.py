#!/usr/bin/env python3
"""
Scopus文献检索工具
使用Elsevier Scopus API检索文献（包含Embase索引内容）
"""

import sys
import json
import urllib.request
import urllib.parse
import time
from typing import List, Dict, Optional

# Scopus API配置
SCOPUS_API_URL = "https://api.elsevier.com/content/search/scopus"
# API Key
API_KEY = "f0552939d5fbc72584702484ca23474d"


def search_scopus(query: str, max_results: int = 25) -> Dict:
    """
    检索Scopus数据库文献
    
    Args:
        query: 检索关键词（支持Scopus语法）
        max_results: 最大返回结果数
    
    Returns:
        包含检索结果的字典
    """
    # 构建检索参数
    search_params = {
        "query": query,
        "count": min(max_results, 25),
        "view": "COMPLETE"
    }
    
    headers = {
        "X-ELS-APIKey": API_KEY,
        "Accept": "application/json"
    }
    
    try:
        req = urllib.request.Request(
            f"{SCOPUS_API_URL}?{urllib.parse.urlencode(search_params)}",
            headers=headers,
            method="GET"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return parse_scopus_results(result, query)
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


def parse_scopus_results(result: Dict, query: str) -> Dict:
    """
    解析Scopus检索结果
    """
    entries = result.get("search-results", {}).get("entry", [])
    
    results = []
    for entry in entries:
        # 提取作者信息
        authors = []
        author_list = entry.get("author", [])
        if isinstance(author_list, dict):
            author_list = [author_list]
        for author in author_list[:5]:
            if isinstance(author, dict):
                authors.append(author.get("authname", ""))
        
        # 提取DOI
        doi = entry.get("prism:doi", "")
        
        # 提取期刊
        journal = entry.get("prism:publicationName", "N/A")
        
        # 提取发表日期
        pub_date = entry.get("prism:coverDate", "N/A")
        
        # 提取PMID（如果有）
        pmid = ""
        identifiers = entry.get("pubmed-id", "")
        if identifiers:
            pmid = identifiers
        
        results.append({
            "scopus_id": entry.get("eid", "N/A"),
            "pmid": pmid,
            "title": entry.get("dc:title", "N/A"),
            "authors": authors,
            "journal": journal,
            "pubdate": pub_date,
            "doi": doi,
            "citedby_count": entry.get("citedby-count", "0"),
            "url": entry.get("link", [{}])[0].get("@href", "") if isinstance(entry.get("link", []), list) else ""
        })
    
    return {
        "query": query,
        "database": "Scopus",
        "count": len(results),
        "results": results
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: scopus_search.py <query> [max_results]", file=sys.stderr)
        print("  query: Scopus search query", file=sys.stderr)
        print("  max_results: Maximum number of results (default: 25, max: 25)", file=sys.stderr)
        print("", file=sys.stderr)
        print("Example:", file=sys.stderr)
        print('  python3 scopus_search.py "TITLE-ABS-KEY(Fanconi syndrome) AND (diagnosis OR treatment) AND PUBYEAR > 2014" 25', file=sys.stderr)
        sys.exit(1)
    
    query = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    
    # 遵守API速率限制
    time.sleep(0.5)
    
    result = search_scopus(query, max_results)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
