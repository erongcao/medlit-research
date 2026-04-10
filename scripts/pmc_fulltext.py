#!/usr/bin/env python3
"""
PubMed Central (PMC) 和 Elsevier ScienceDirect 全文获取工具
自动识别并下载开放获取文献的全文
"""

import sys
import json
import urllib.request
import urllib.parse
import time
import os
from typing import Dict, Optional
from xml.etree import ElementTree as ET

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PMC_BASE_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles"
ELSEVIER_API_URL = "https://api.elsevier.com/content/article"
TOOL_NAME = "medlit-research"
EMAIL = os.environ.get("NCBI_EMAIL", "caoyirong@gmail.com")


def get_elsevier_api_key() -> Optional[str]:
    """获取 Elsevier API Key"""
    return os.environ.get("EMBASE_API_KEY") or os.environ.get("ELSEVIER_API_KEY")


def check_article_availability(pmid: str) -> Dict:
    """
    检查文献的可获取性（包括PMC和Elsevier）
    """
    # 首先检查PMC
    elink_params = {
        "dbfrom": "pubmed",
        "db": "pmc",
        "id": pmid,
        "retmode": "json",
        "tool": TOOL_NAME,
        "email": EMAIL
    }
    
    elink_url = f"{NCBI_BASE_URL}/elink.fcgi"
    
    try:
        data = urllib.parse.urlencode(elink_params).encode('utf-8')
        with urllib.request.urlopen(elink_url, data=data, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        # 解析PMC ID
        pmcid = None
        linksets = result.get("linksets", [])
        if linksets:
            linksetdbs = linksets[0].get("linksetdbs", [])
            for db in linksetdbs:
                if db.get("dbto") == "pmc":
                    links = db.get("links", [])
                    if links:
                        pmcid = f"PMC{links[0]}"
                        break
        
        if pmcid:
            return {
                "pmid": pmid,
                "pmcid": pmcid,
                "availability": "pmc_free",
                "full_text_url": f"{PMC_BASE_URL}/{pmcid}/",
                "source": "PMC",
                "doi": None
            }
        
        # PMC没有，检查是否有DOI可以通过Elsevier获取
        # 获取文章摘要信息
        esummary_params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "json",
            "tool": TOOL_NAME,
            "email": EMAIL
        }
        
        esummary_url = f"{NCBI_BASE_URL}/esummary.fcgi"
        data = urllib.parse.urlencode(esummary_params).encode('utf-8')
        with urllib.request.urlopen(esummary_url, data=data, timeout=30) as response:
            summary = json.loads(response.read().decode('utf-8'))
        
        article = summary.get("result", {}).get(pmid, {})
        doi = article.get("elocationid", "")
        if doi.startswith("doi:"):
            doi = doi[4:].strip()
        
        journal = article.get("fulljournalname", "")
        
        # 检查是否是Elsevier期刊
        elsevier_journals = ["cell", "lancet", "gastroenterology", "cancer research", 
                            "surgery", "annals of oncology", "journal of hepatology",
                            "cell reports", "eclinicalmedicine", "thelancet"]
        
        is_elsevier = any(ej.lower() in journal.lower() for ej in elsevier_journals)
        
        if doi and is_elsevier and get_elsevier_api_key():
            return {
                "pmid": pmid,
                "pmcid": None,
                "doi": doi,
                "availability": "elsevier_api",
                "full_text_url": f"{ELSEVIER_API_URL}/doi/{doi}",
                "source": "Elsevier",
                "journal": journal
            }
        
        return {
            "pmid": pmid,
            "pmcid": None,
            "doi": doi,
            "availability": "abstract_only",
            "full_text_url": None,
            "source": None
        }
            
    except Exception as e:
        return {
            "pmid": pmid,
            "pmcid": None,
            "availability": "error",
            "full_text_url": None,
            "error": str(e)
        }


def fetch_elsevier_fulltext(doi: str) -> Dict:
    """
    通过 Elsevier ScienceDirect API 获取全文
    """
    api_key = get_elsevier_api_key()
    if not api_key:
        return {"error": "Elsevier API Key not configured"}
    
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json",
        "User-Agent": "medlit-research/1.0"
    }
    
    try:
        url = f"{ELSEVIER_API_URL}/doi/{doi}"
        
        if HAS_REQUESTS:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
        else:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        
        # 解析返回的数据
        ft_response = data.get("full-text-retrieval-response", {})
        
        # 提取基本信息
        coredata = ft_response.get("coredata", {})
        title = coredata.get("dc:title", "N/A")
        abstract = coredata.get("dc:description", "N/A")
        
        # 提取正文内容
        original_text = ft_response.get("originalText", "")
        
        # 解析章节（如果可能）
        sections = {}
        
        return {
            "doi": doi,
            "title": title,
            "abstract": abstract,
            "full_text": original_text[:50000],
            "sections": sections,
            "word_count": len(original_text.split()),
            "source": "Elsevier ScienceDirect"
        }
        
    except Exception as e:
        return {"doi": doi, "error": f"Failed to fetch from Elsevier: {str(e)}"}


def fetch_pmc_fulltext(pmcid: str) -> Dict:
    """获取PMC全文内容"""
    efetch_params = {
        "db": "pmc",
        "id": pmcid.replace("PMC", ""),
        "retmode": "xml",
        "tool": TOOL_NAME,
        "email": EMAIL
    }
    
    efetch_url = f"{NCBI_BASE_URL}/efetch.fcgi"
    
    try:
        data = urllib.parse.urlencode(efetch_params).encode('utf-8')
        with urllib.request.urlopen(efetch_url, data=data, timeout=60) as response:
            xml_content = response.read().decode('utf-8')
        
        # 解析XML
        root = ET.fromstring(xml_content)
        
        article = root.find('.//article')
        if article is None:
            return {"pmcid": pmcid, "error": "Article not found in XML"}
        
        # 提取标题
        title_elem = article.find('.//article-title')
        title = "".join(title_elem.itertext()) if title_elem is not None else "N/A"
        
        # 提取摘要
        abstract_elem = article.find('.//abstract')
        abstract = ""
        if abstract_elem is not None:
            abstract = "".join(abstract_elem.itertext())
        
        # 提取全文段落
        body = article.find('.//body')
        full_text = ""
        sections = {}
        
        if body is not None:
            paragraphs = body.findall('.//p')
            full_text = "\n\n".join(["".join(p.itertext()) for p in paragraphs])
            
            for sec in body.findall('.//sec'):
                sec_title = sec.find('title')
                if sec_title is not None:
                    sec_name = sec_title.text.lower() if sec_title.text else ""
                    sec_text = "".join(sec.itertext())
                    
                    if any(x in sec_name for x in ['introduction', 'background']):
                        sections['introduction'] = sec_text
                    elif 'method' in sec_name:
                        sections['methods'] = sec_text
                    elif 'result' in sec_name:
                        sections['results'] = sec_text
                    elif 'discussion' in sec_name:
                        sections['discussion'] = sec_text
                    elif 'conclusion' in sec_name:
                        sections['conclusion'] = sec_text
        
        return {
            "pmcid": pmcid,
            "title": title,
            "abstract": abstract,
            "full_text": full_text[:50000],
            "sections": sections,
            "word_count": len(full_text.split()),
            "source": "PubMed Central"
        }
        
    except Exception as e:
        return {
            "pmcid": pmcid,
            "error": f"Failed to fetch full text: {str(e)}"
        }


def analyze_fulltext_for_appraisal(fulltext_data: Dict) -> Dict:
    """分析全文内容，提取关键信息用于批判性评价"""
    sections = fulltext_data.get("sections", {})
    full_text = fulltext_data.get("full_text", "")
    
    analysis = {
        "study_design": None,
        "sample_size": None,
        "study_duration": None,
        "intervention": None,
        "primary_outcome": None,
        "statistical_methods": [],
        "key_findings": [],
        "limitations_stated": [],
        "funding": None,
        "conflicts_of_interest": None
    }
    
    # 从方法部分提取信息
    methods = sections.get("methods", "")
    if methods:
        methods_lower = methods.lower()
        if "randomized" in methods_lower or "randomised" in methods_lower:
            analysis["study_design"] = "RCT"
        elif "cohort" in methods_lower:
            analysis["study_design"] = "cohort"
        elif "case-control" in methods_lower or "case control" in methods_lower:
            analysis["study_design"] = "case_control"
        elif "cross-sectional" in methods_lower:
            analysis["study_design"] = "cross_sectional"
        
        import re
        sample_match = re.search(r'(\d+)\s*(patients|subjects|participants|mice|rats|animals)', methods, re.IGNORECASE)
        if sample_match:
            analysis["sample_size"] = int(sample_match.group(1))
    
    # 从结果部分提取关键发现
    results = sections.get("results", "")
    if results:
        sentences = results.split('.')
        for sent in sentences[:10]:
            if any(x in sent.lower() for x in ['significant', 'increased', 'decreased', 'associated', 'correlated', 'demonstrated']):
                analysis["key_findings"].append(sent.strip())
    
    # 从讨论/结论提取局限性
    discussion = sections.get("discussion", "")
    if discussion and "limitation" in discussion.lower():
        limitation_idx = discussion.lower().find("limitation")
        if limitation_idx > 0:
            limit_section = discussion[limitation_idx:limitation_idx+1000]
            analysis["limitations_stated"].append(limit_section.strip())
    
    return analysis


def main():
    if len(sys.argv) < 2:
        print("Usage: pmc_fulltext.py <pmid_or_pmcid_or_doi>", file=sys.stderr)
        print("  pmid_or_pmcid_or_doi: PubMed ID, PMC ID, or DOI", file=sys.stderr)
        sys.exit(1)
    
    article_id = sys.argv[1]
    
    # 判断是PMID、PMC ID还是DOI
    if article_id.startswith("PMC"):
        # 直接获取PMC全文
        pmcid = article_id
        time.sleep(0.34)
        fulltext_data = fetch_pmc_fulltext(pmcid)
        source = "PMC"
        
    elif article_id.startswith("10."):
        # DOI，尝试Elsevier
        if not get_elsevier_api_key():
            print(json.dumps({"error": "Elsevier API Key not configured"}, indent=2))
            sys.exit(1)
        fulltext_data = fetch_elsevier_fulltext(article_id)
        source = "Elsevier"
        
    else:
        # 假设是PMID，检查可用性
        pmid = article_id
        availability = check_article_availability(pmid)
        
        if availability.get("availability") == "pmc_free":
            pmcid = availability["pmcid"]
            time.sleep(0.34)
            fulltext_data = fetch_pmc_fulltext(pmcid)
            source = "PMC"
            
        elif availability.get("availability") == "elsevier_api":
            doi = availability["doi"]
            fulltext_data = fetch_elsevier_fulltext(doi)
            source = "Elsevier"
            
        else:
            print(json.dumps({
                "pmid": pmid,
                "status": "not_available",
                "message": "Full text not available",
                "availability": availability
            }, indent=2, ensure_ascii=False))
            sys.exit(0)
    
    if "error" in fulltext_data:
        print(json.dumps(fulltext_data, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    # 分析全文
    analysis = analyze_fulltext_for_appraisal(fulltext_data)
    
    result = {
        "status": "success",
        "source": source,
        "article_info": fulltext_data,
        "analysis": analysis
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
