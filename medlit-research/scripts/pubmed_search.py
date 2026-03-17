#!/usr/bin/env python3
"""
PubMed文献检索工具
使用NCBI E-utilities API检索PubMed文献
"""

import sys
import json
import urllib.request
import urllib.parse
import time
from typing import List, Dict, Optional

# NCBI API配置
NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL_NAME = "medlit-research"
EMAIL = "user@example.com"  # 用户应替换为自己的邮箱


def search_pubmed(query: str, max_results: int = 20, sort: str = "relevance") -> Dict:
    """
    检索PubMed文献
    
    Args:
        query: 检索关键词（支持PubMed语法）
        max_results: 最大返回结果数
        sort: 排序方式 (relevance, date)
    
    Returns:
        包含检索结果的字典
    """
    # 构建esearch请求
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": sort,
        "retmode": "json",
        "tool": TOOL_NAME,
        "email": EMAIL
    }
    
    search_url = f"{NCBI_BASE_URL}/esearch.fcgi"
    search_data = urllib.parse.urlencode(search_params).encode('utf-8')
    
    try:
        with urllib.request.urlopen(search_url, data=search_data, timeout=30) as response:
            search_result = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}
    
    idlist = search_result.get("esearchresult", {}).get("idlist", [])
    
    if not idlist:
        return {"query": query, "count": 0, "results": []}
    
    # 获取文献详情
    return fetch_pubmed_details(idlist, query)


def fetch_pubmed_details(pmids: List[str], query: str = "") -> Dict:
    """
    获取PubMed文献详细信息
    
    Args:
        pmids: PubMed ID列表
        query: 原始检索词
    
    Returns:
        包含文献详情的字典
    """
    if not pmids:
        return {"query": query, "count": 0, "results": []}
    
    # 构建esummary请求
    summary_params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
        "tool": TOOL_NAME,
        "email": EMAIL
    }
    
    summary_url = f"{NCBI_BASE_URL}/esummary.fcgi"
    summary_data = urllib.parse.urlencode(summary_params).encode('utf-8')
    
    try:
        with urllib.request.urlopen(summary_url, data=summary_data, timeout=30) as response:
            summary_result = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": f"Fetch details failed: {str(e)}"}
    
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
                "abstract_available": bool(article.get("attributes", [])),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })
    
    return {
        "query": query,
        "count": len(results),
        "results": results
    }


def fetch_abstract(pmid: str) -> Dict:
    """
    获取单篇文献的摘要
    
    Args:
        pmid: PubMed ID
    
    Returns:
        包含摘要的字典
    """
    fetch_params = {
        "db": "pubmed",
        "id": pmid,
        "rettype": "abstract",
        "retmode": "text",
        "tool": TOOL_NAME,
        "email": EMAIL
    }
    
    fetch_url = f"{NCBI_BASE_URL}/efetch.fcgi"
    fetch_data = urllib.parse.urlencode(fetch_params).encode('utf-8')
    
    try:
        with urllib.request.urlopen(fetch_url, data=fetch_data, timeout=30) as response:
            abstract = response.read().decode('utf-8')
            return {"pmid": pmid, "abstract": abstract}
    except Exception as e:
        return {"pmid": pmid, "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print("Usage: pubmed_search.py <query> [max_results] [sort]", file=sys.stderr)
        print("  query: PubMed search query", file=sys.stderr)
        print("  max_results: Maximum number of results (default: 20)", file=sys.stderr)
        print("  sort: Sort by 'relevance' or 'date' (default: relevance)", file=sys.stderr)
        sys.exit(1)
    
    query = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    sort = sys.argv[3] if len(sys.argv) > 3 else "relevance"
    
    # 遵守NCBI速率限制
    time.sleep(0.34)
    
    result = search_pubmed(query, max_results, sort)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
