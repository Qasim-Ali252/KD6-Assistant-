"""
Advanced Multi-Source Search Engine
Combines multiple search sources for comprehensive answers
"""
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import hashlib

class AdvancedSearchEngine:
    """Advanced search with multiple sources and caching"""
    
    def __init__(self, config):
        self.config = config
        self.cache = {}  # In-memory cache
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
        
        # API endpoints
        self.ddg_api = "https://api.duckduckgo.com/"
        self.wikipedia_api = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        return hashlib.md5(query.lower().encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if 'timestamp' not in cache_entry:
            return False
        
        cached_time = datetime.fromisoformat(cache_entry['timestamp'])
        return datetime.now() - cached_time < self.cache_duration
    
    def search_duckduckgo(self, query: str) -> Dict:
        """Search DuckDuckGo Instant Answer API"""
        try:
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            
            response = requests.get(self.ddg_api, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            return {
                'source': 'DuckDuckGo',
                'abstract': data.get('Abstract', ''),
                'abstract_source': data.get('AbstractSource', ''),
                'abstract_url': data.get('AbstractURL', ''),
                'definition': data.get('Definition', ''),
                'related_topics': [
                    {'text': t.get('Text', ''), 'url': t.get('FirstURL', '')}
                    for t in data.get('RelatedTopics', [])[:3]
                    if isinstance(t, dict) and 'Text' in t
                ],
                'success': True
            }
        except Exception as e:
            return {'source': 'DuckDuckGo', 'success': False, 'error': str(e)}
    
    def search_wikipedia(self, query: str) -> Dict:
        """Search Wikipedia API"""
        try:
            # Clean query for Wikipedia
            search_term = query.replace('what is ', '').replace('who is ', '').strip()
            
            # Wikipedia summary endpoint
            url = f"{self.wikipedia_api}{search_term.replace(' ', '_')}"
            
            # Add proper headers to avoid 403
            headers = {
                'User-Agent': 'KD6-Assistant/1.0 (Educational AI Assistant)',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            return {
                'source': 'Wikipedia',
                'title': data.get('title', ''),
                'extract': data.get('extract', ''),
                'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'thumbnail': data.get('thumbnail', {}).get('source', ''),
                'success': True
            }
        except Exception as e:
            return {'source': 'Wikipedia', 'success': False, 'error': str(e)}
    
    def multi_source_search(self, query: str) -> Dict:
        """
        Search multiple sources and combine results
        
        Returns comprehensive information from multiple sources
        """
        # Check cache first
        cache_key = self._get_cache_key(query)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            print(f"✓ Using cached results for: {query}")
            return self.cache[cache_key]
        
        print(f"🔍 Searching multiple sources for: {query}")
        
        results = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'sources': []
        }
        
        # Search DuckDuckGo
        ddg_result = self.search_duckduckgo(query)
        if ddg_result.get('success'):
            results['sources'].append(ddg_result)
            print(f"  ✓ DuckDuckGo: Found information")
        else:
            print(f"  ✗ DuckDuckGo: {ddg_result.get('error', 'No results')}")
        
        # Search Wikipedia
        wiki_result = self.search_wikipedia(query)
        if wiki_result.get('success'):
            results['sources'].append(wiki_result)
            print(f"  ✓ Wikipedia: Found article")
        else:
            print(f"  ✗ Wikipedia: {wiki_result.get('error', 'No results')}")
        
        # Cache results
        self.cache[cache_key] = results
        
        return results
    
    def format_multi_source_results(self, results: Dict) -> str:
        """
        Format multi-source results for LLM
        
        Combines information from multiple sources with citations
        """
        if not results.get('sources'):
            return "No web results found. Providing answer based on existing knowledge."
        
        formatted = []
        formatted.append("=== INFORMATION FROM MULTIPLE SOURCES ===\n")
        
        for source_data in results['sources']:
            source_name = source_data.get('source', 'Unknown')
            
            if source_name == 'Wikipedia' and source_data.get('extract'):
                formatted.append(f"From Wikipedia:")
                formatted.append(f"{source_data['extract']}")
                if source_data.get('url'):
                    formatted.append(f"Source: {source_data['url']}")
                formatted.append("")
            
            elif source_name == 'DuckDuckGo':
                if source_data.get('abstract'):
                    formatted.append(f"From {source_data.get('abstract_source', 'DuckDuckGo')}:")
                    formatted.append(f"{source_data['abstract']}")
                    formatted.append("")
                
                if source_data.get('definition'):
                    formatted.append(f"Definition:")
                    formatted.append(f"{source_data['definition']}")
                    formatted.append("")
                
                if source_data.get('related_topics'):
                    formatted.append("Related Information:")
                    for i, topic in enumerate(source_data['related_topics'][:2], 1):
                        formatted.append(f"  {i}. {topic['text'][:100]}")
                    formatted.append("")
        
        formatted.append("=== END SOURCES ===")
        formatted.append("\nInstructions: Synthesize the above information into a clear, accurate answer. Cite sources when appropriate.")
        
        return '\n'.join(formatted)
    
    def verify_facts(self, claim: str, sources: List[Dict]) -> Dict:
        """
        Verify a claim against multiple sources
        
        Returns confidence level and supporting evidence
        """
        supporting_sources = []
        contradicting_sources = []
        
        claim_lower = claim.lower()
        
        for source in sources:
            source_text = ""
            
            if source.get('source') == 'Wikipedia':
                source_text = source.get('extract', '').lower()
            elif source.get('source') == 'DuckDuckGo':
                source_text = source.get('abstract', '').lower()
            
            # Simple keyword matching for verification
            # In production, use NLP/semantic similarity
            claim_keywords = set(claim_lower.split())
            source_keywords = set(source_text.split())
            
            overlap = len(claim_keywords & source_keywords)
            
            if overlap > len(claim_keywords) * 0.5:  # 50% keyword overlap
                supporting_sources.append(source.get('source'))
        
        confidence = len(supporting_sources) / max(len(sources), 1)
        
        return {
            'claim': claim,
            'confidence': confidence,
            'supporting_sources': supporting_sources,
            'contradicting_sources': contradicting_sources,
            'verified': confidence > 0.5
        }
    
    def get_advanced_context(self, query: str) -> Optional[str]:
        """
        Get advanced search context with multi-source verification
        
        Args:
            query: User's question
            
        Returns:
            Formatted multi-source results or None
        """
        results = self.multi_source_search(query)
        
        if not results.get('sources'):
            return None
        
        formatted = self.format_multi_source_results(results)
        return formatted
    
    def clear_cache(self):
        """Clear the search cache"""
        self.cache = {}
        print("✓ Search cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        valid_entries = sum(1 for entry in self.cache.values() if self._is_cache_valid(entry))
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.cache) - valid_entries
        }
