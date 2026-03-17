#!/usr/bin/env python3
"""
Brave Search API 工具
用于医学文献补充检索
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Optional

BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"

class BraveSearcher:
    """Brave Search 检索器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化，优先从环境变量获取API Key"""
        self.api_key = api_key or os.environ.get("BRAVE_API_KEY", "")
        if not self.api_key:
            raise ValueError("Brave API Key 未配置。请设置 BRAVE_API_KEY 环境变量")
    
    def search(self, query: str, count: int = 10, 
               offset: int = 0,
               search_type: str = "web") -> Dict:
        """
        执行Brave搜索
        
        Args:
            query: 搜索词
            count: 结果数量（最大20）
            offset: 分页偏移
            search_type: 搜索类型 (web, news, images)
        """
        params = {
            "q": query,
            "count": min(count, 20),
            "offset": offset
        }
        
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        
        try:
            url = f"{BRAVE_API_URL}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # 解析结果
            results = []
            if 'web' in data and 'results' in data['web']:
                for item in data['web']['results']:
                    results.append({
                        "title": item.get('title', 'N/A'),
                        "url": item.get('url', ''),
                        "description": item.get('description', '')[:200],
                        "source": "Brave Search"
                    })
            
            return {
                "query": query,
                "total_count": data.get('web', {}).get('total', len(results)),
                "returned_count": len(results),
                "results": results,
                "status": "success"
            }
            
        except urllib.error.HTTPError as e:
            return {
                "query": query,
                "status": "error",
                "error": f"HTTP {e.code}: {e.reason}",
                "message": "API Key可能无效或已过期"
            }
        except Exception as e:
            return {
                "query": query,
                "status": "error",
                "error": str(e)
            }
    
    def search_medical(self, query: str, count: int = 10) -> Dict:
        """
        医学专用搜索（添加医学关键词优化）
        """
        medical_query = f"{query} medical clinical research"
        return self.search(medical_query, count)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("Usage: brave_search.py <query> [options]")
        print("")
        print("Options:")
        print("  --count N    结果数量 (默认: 10, 最大: 20)")
        print("  --medical    医学优化搜索")
        print("")
        print("Examples:")
        print('  brave_search.py "autoimmune hepatitis" --count 5')
        print('  brave_search.py "diabetes treatment" --medical')
        sys.exit(1)
    
    query = sys.argv[1]
    count = 10
    medical_mode = False
    
    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--count" and i + 1 < len(sys.argv):
            count = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--medical":
            medical_mode = True
            i += 1
        else:
            i += 1
    
    try:
        searcher = BraveSearcher()
        
        if medical_mode:
            result = searcher.search_medical(query, count)
        else:
            result = searcher.search(query, count)
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except ValueError as e:
        print(json.dumps({
            "status": "error",
            "error": str(e),
            "setup_instructions": [
                "1. 获取Brave Search API Key: https://brave.com/search/api/",
                "2. 设置环境变量: export BRAVE_API_KEY='your_key'",
                "3. 或使用: BRAVE_API_KEY='your_key' python3 brave_search.py 'query'"
            ]
        }, indent=2))


if __name__ == "__main__":
    main()
