"""
Web Search Integration for Knowledge Enhancement
Enables KD6 to search the internet for current information
"""
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime

class WebSearchEngine:
    """Handles web searches for knowledge enhancement"""
    
    def __init__(self, config):
        self.config = config
        # Using DuckDuckGo Instant Answer API (free, no API key needed)
        self.ddg_api = "https://api.duckduckgo.com/"
        
    def should_search(self, user_query: str) -> bool:
        """
        Determine if a query requires web search
        
        Returns True for:
        - Current events, news, dates
        - Technical specifications, versions
        - Factual questions
        - "What is", "How to", "When did", etc.
        """
        query_lower = user_query.lower()
        
        # Trigger words that indicate need for search
        search_triggers = [
            'what is', 'what are', 'who is', 'who are',
            'when did', 'when was', 'when will',
            'how to', 'how do', 'how does',
            'why is', 'why are', 'why did',
            'where is', 'where are', 'where can',
            'latest', 'current', 'recent', 'today',
            'news', 'update', 'version',
            'price', 'cost', 'worth',
            'definition', 'meaning', 'explain',
            'tell me about', 'information about',
            'search for', 'look up', 'find out',
            'road map', 'roadmap', 'guide', 'tutorial',
            'learn', 'learning', 'study',
            'complete', 'full', 'entire', 'comprehensive',
            'list of', 'steps', 'process'
        ]
        
        # Check if query contains search triggers
        for trigger in search_triggers:
            if trigger in query_lower:
                return True
        
        # Check for question marks (likely a question)
        if '?' in user_query:
            return True
        
        return False
    
    def search(self, query: str, max_results: int = 3) -> Dict:
        """
        Search the web for information
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search results and metadata
        """
        try:
            # Use DuckDuckGo Instant Answer API
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            
            response = requests.get(self.ddg_api, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            results = {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'abstract': data.get('Abstract', ''),
                'abstract_source': data.get('AbstractSource', ''),
                'abstract_url': data.get('AbstractURL', ''),
                'definition': data.get('Definition', ''),
                'definition_source': data.get('DefinitionSource', ''),
                'related_topics': [],
                'success': True
            }
            
            # Extract related topics
            for topic in data.get('RelatedTopics', [])[:max_results]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results['related_topics'].append({
                        'text': topic.get('Text', ''),
                        'url': topic.get('FirstURL', '')
                    })
            
            return results
            
        except Exception as e:
            print(f"Web search error: {e}")
            return {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }
    
    def format_results(self, results: Dict) -> str:
        """
        Format search results into readable text
        
        Args:
            results: Search results dictionary
            
        Returns:
            Formatted string for LLM context
        """
        if not results.get('success'):
            return "Web search failed. Providing answer based on existing knowledge."
        
        formatted = []
        
        # Add abstract if available
        if results.get('abstract'):
            formatted.append(f"Summary: {results['abstract']}")
            if results.get('abstract_source'):
                formatted.append(f"Source: {results['abstract_source']}")
        
        # Add definition if available
        if results.get('definition'):
            formatted.append(f"Definition: {results['definition']}")
            if results.get('definition_source'):
                formatted.append(f"Source: {results['definition_source']}")
        
        # Add related information
        if results.get('related_topics'):
            formatted.append("\nRelated Information:")
            for i, topic in enumerate(results['related_topics'][:3], 1):
                formatted.append(f"{i}. {topic['text']}")
        
        if not formatted:
            return "No specific web results found. Providing answer based on existing knowledge."
        
        return '\n'.join(formatted)
    
    def get_context_for_llm(self, user_query: str) -> Optional[str]:
        """
        Get web search context for LLM if needed
        
        Args:
            user_query: User's question
            
        Returns:
            Formatted search results or None
        """
        if not self.should_search(user_query):
            return None
        
        print(f"🔍 Searching web for: {user_query}")
        results = self.search(user_query)
        
        if results.get('success'):
            formatted = self.format_results(results)
            print(f"✓ Found web information")
            return formatted
        else:
            print(f"⚠ Web search failed, using existing knowledge")
            return None
