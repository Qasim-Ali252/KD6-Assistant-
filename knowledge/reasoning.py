"""
Chain-of-Thought Reasoning Module
Enables step-by-step reasoning for complex questions
"""
from typing import List, Dict, Optional

class ReasoningEngine:
    """Handles complex reasoning with chain-of-thought"""
    
    def __init__(self, config):
        self.config = config
    
    def requires_reasoning(self, query: str) -> bool:
        """
        Determine if query requires step-by-step reasoning
        
        Returns True for:
        - Multi-step problems
        - Comparison questions
        - Cause-and-effect questions
        - Complex explanations
        """
        query_lower = query.lower()
        
        reasoning_triggers = [
            'why', 'how does', 'explain',
            'compare', 'difference between',
            'pros and cons', 'advantages and disadvantages',
            'step by step', 'process',
            'cause', 'effect', 'result',
            'analyze', 'evaluate',
            'solve', 'calculate',
            'relationship between'
        ]
        
        return any(trigger in query_lower for trigger in reasoning_triggers)
    
    def build_reasoning_prompt(self, query: str, web_context: Optional[str] = None) -> str:
        """
        Build a prompt that encourages chain-of-thought reasoning
        
        Args:
            query: User's question
            web_context: Optional web search results
            
        Returns:
            Enhanced prompt with reasoning instructions
        """
        prompt_parts = []
        
        prompt_parts.append("=== REASONING TASK ===")
        prompt_parts.append(f"Question: {query}")
        prompt_parts.append("")
        
        if web_context:
            prompt_parts.append(web_context)
            prompt_parts.append("")
        
        prompt_parts.append("=== REASONING INSTRUCTIONS ===")
        prompt_parts.append("Think through this step-by-step:")
        prompt_parts.append("1. Break down the question into components")
        prompt_parts.append("2. Consider relevant facts and principles")
        prompt_parts.append("3. Apply logical reasoning")
        prompt_parts.append("4. Draw conclusions")
        prompt_parts.append("5. Provide a clear, comprehensive answer")
        prompt_parts.append("")
        prompt_parts.append("Format your response naturally, explaining your reasoning as you go.")
        prompt_parts.append("=== END INSTRUCTIONS ===")
        
        return '\n'.join(prompt_parts)
    
    def identify_question_type(self, query: str) -> str:
        """
        Identify the type of question for tailored reasoning
        
        Returns: 'factual', 'procedural', 'analytical', 'comparative', 'causal'
        """
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['what is', 'what are', 'who is', 'when']):
            return 'factual'
        
        if any(word in query_lower for word in ['how to', 'how do', 'steps', 'process']):
            return 'procedural'
        
        if any(word in query_lower for word in ['compare', 'difference', 'versus', 'vs']):
            return 'comparative'
        
        if any(word in query_lower for word in ['why', 'cause', 'reason', 'because']):
            return 'causal'
        
        if any(word in query_lower for word in ['analyze', 'evaluate', 'assess', 'explain']):
            return 'analytical'
        
        return 'general'
    
    def get_reasoning_template(self, question_type: str) -> str:
        """
        Get reasoning template based on question type
        
        Args:
            question_type: Type of question
            
        Returns:
            Template for structuring the answer
        """
        templates = {
            'factual': (
                "Provide a clear definition or fact, then elaborate with:\n"
                "- Key characteristics\n"
                "- Historical context (if relevant)\n"
                "- Current significance"
            ),
            'procedural': (
                "Explain the process step-by-step:\n"
                "1. Prerequisites or requirements\n"
                "2. Step-by-step instructions\n"
                "3. Tips or common pitfalls\n"
                "4. Expected outcome"
            ),
            'comparative': (
                "Compare systematically:\n"
                "- Similarities between the items\n"
                "- Key differences\n"
                "- Pros and cons of each\n"
                "- Conclusion or recommendation"
            ),
            'causal': (
                "Explain the cause-and-effect relationship:\n"
                "- The underlying cause(s)\n"
                "- The mechanism or process\n"
                "- The resulting effect(s)\n"
                "- Additional factors or context"
            ),
            'analytical': (
                "Provide a thorough analysis:\n"
                "- Break down the components\n"
                "- Examine each aspect\n"
                "- Consider different perspectives\n"
                "- Synthesize into a conclusion"
            ),
            'general': (
                "Provide a comprehensive answer:\n"
                "- Address the main question\n"
                "- Provide supporting details\n"
                "- Include relevant context\n"
                "- Conclude clearly"
            )
        }
        
        return templates.get(question_type, templates['general'])
    
    def enhance_prompt_with_reasoning(self, query: str, base_prompt: str, web_context: Optional[str] = None) -> str:
        """
        Enhance prompt with reasoning instructions
        
        Args:
            query: User's question
            base_prompt: Base prompt to enhance
            web_context: Optional web search results
            
        Returns:
            Enhanced prompt with reasoning guidance
        """
        if not self.requires_reasoning(query):
            return base_prompt
        
        question_type = self.identify_question_type(query)
        template = self.get_reasoning_template(question_type)
        
        enhanced = []
        enhanced.append(base_prompt)
        enhanced.append("")
        enhanced.append("=== REASONING GUIDANCE ===")
        enhanced.append(f"Question Type: {question_type.title()}")
        enhanced.append("")
        enhanced.append(template)
        enhanced.append("")
        enhanced.append("Think through this carefully and provide a well-reasoned answer.")
        enhanced.append("=== END GUIDANCE ===")
        
        return '\n'.join(enhanced)
    
    def extract_reasoning_steps(self, response: str) -> List[str]:
        """
        Extract reasoning steps from a response
        
        Useful for analyzing the AI's reasoning process
        """
        steps = []
        
        # Look for numbered steps
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                steps.append(line)
        
        return steps
    
    def validate_reasoning(self, query: str, response: str, web_context: Optional[str] = None) -> Dict:
        """
        Validate the reasoning in a response
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'has_reasoning': False,
            'addresses_question': False,
            'uses_sources': False,
            'logical_flow': False,
            'completeness': 0.0
        }
        
        response_lower = response.lower()
        query_lower = query.lower()
        
        # Check if response has reasoning indicators
        reasoning_indicators = ['because', 'therefore', 'thus', 'since', 'as a result', 'this means']
        validation['has_reasoning'] = any(indicator in response_lower for indicator in reasoning_indicators)
        
        # Check if response addresses the question
        query_keywords = set(query_lower.split())
        response_keywords = set(response_lower.split())
        overlap = len(query_keywords & response_keywords)
        validation['addresses_question'] = overlap > len(query_keywords) * 0.3
        
        # Check if response uses sources (if web context provided)
        if web_context:
            validation['uses_sources'] = 'according to' in response_lower or 'source' in response_lower
        
        # Check logical flow (has multiple sentences)
        sentences = response.split('.')
        validation['logical_flow'] = len(sentences) >= 3
        
        # Calculate completeness score
        completeness_factors = [
            validation['has_reasoning'],
            validation['addresses_question'],
            validation['logical_flow']
        ]
        validation['completeness'] = sum(completeness_factors) / len(completeness_factors)
        
        return validation
