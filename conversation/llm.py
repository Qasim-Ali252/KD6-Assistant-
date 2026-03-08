import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
from knowledge.web_search import WebSearchEngine
from knowledge.advanced_search import AdvancedSearchEngine
from knowledge.reasoning import ReasoningEngine

class ConversationEngine:
    def __init__(self, config):
        self.config = config
        self.api_endpoint = config['api']['llm_endpoint']
        self.api_key = config['api']['llm_api_key']
        
        # Model selection for speed optimization
        self.fast_model = config['api'].get('fast_model', 'llama-3.1-8b-instant')
        self.standard_model = config['api'].get('standard_model', 'llama-3.3-70b-versatile')
        self.use_fast_for_casual = config['api'].get('use_fast_model_for_casual', True)
        
        # Initialize knowledge systems
        self.web_search = WebSearchEngine(config)
        self.advanced_search = AdvancedSearchEngine(config)
        self.reasoning = ReasoningEngine(config)
        
        # Use advanced search if enabled
        self.use_advanced_search = config.get('knowledge', {}).get('advanced_search_enabled', True)
        
        # Track recent topics to avoid repetition
        self.recent_topics: List[Dict] = []
        
        # Track recent responses to avoid repetition
        self.recent_responses: List[str] = []
        
        # Enhanced conversation context - keep more history
        self.conversation_history: List[Dict] = []
        
        # Long-term memory for important facts
        self.important_facts: Dict[str, str] = {}
        
        # User preferences learned from conversation
        self.user_info: Dict[str, any] = {
            'name': None,
            'interests': [],
            'mentioned_people': {},
            'mentioned_places': [],
            'mentioned_things': {}
        }
        
        # Memory manager reference (will be set by main.py)
        self.memory_manager = None
    
    def generate(self, context, emotion, personality, memory, trigger, 
                preference_profile=None, activity=None):
        """Generate response using cloud LLM with enhanced context"""
        
        # Check if we should search the web for this query
        web_context = None
        user_speech = context.get('user_speech', '')
        if user_speech and trigger == 'user_spoke':
            # Use advanced multi-source search if enabled
            if self.use_advanced_search and self.web_search.should_search(user_speech):
                web_context = self.advanced_search.get_advanced_context(user_speech)
            elif self.web_search.should_search(user_speech):
                web_context = self.web_search.get_context_for_llm(user_speech)
        
        # Build prompt with enhanced context
        system_prompt = personality.get_system_prompt()
        
        # Add enhanced thinking instructions
        system_prompt += "\n\nENHANCED THINKING GUIDELINES:"
        system_prompt += "\n- You are a highly intelligent AI assistant with access to multi-source web search"
        system_prompt += "\n- For factual questions, synthesize information from multiple sources"
        system_prompt += "\n- Use chain-of-thought reasoning for complex questions"
        system_prompt += "\n- Think step-by-step through problems"
        system_prompt += "\n- Provide accurate, well-reasoned answers with citations"
        system_prompt += "\n- Verify facts across multiple sources when available"
        system_prompt += "\n- Admit when you're uncertain and explain your reasoning"
        system_prompt += "\n- Break down complex topics into understandable explanations"
        system_prompt += "\n- Show your reasoning process for analytical questions"
        
        # Add conversation guidelines to system prompt
        system_prompt += "\n\nCONVERSATION GUIDELINES:"
        system_prompt += "\n- Give direct, natural responses without meta-commentary"
        system_prompt += "\n- Don't repeatedly ask if the user is okay or seems distracted"
        system_prompt += "\n- Respond to what the user actually said, not what you think they meant"
        system_prompt += "\n- Keep responses concise and conversational (1-3 sentences for casual chat)"
        system_prompt += "\n- For knowledge questions, provide detailed, accurate answers"
        system_prompt += "\n- Don't repeat yourself or say similar things you've said recently"
        system_prompt += "\n- If the user gives you information, acknowledge it naturally and move on"
        system_prompt += "\n- Remember important facts the user tells you (names, places, interests)"
        
        # Add user information to system prompt if available
        if self.user_info['name']:
            system_prompt += f"\n- User's name: {self.user_info['name']}"
        if self.user_info['interests']:
            system_prompt += f"\n- User's interests: {', '.join(self.user_info['interests'][:5])}"
        if self.user_info['mentioned_people']:
            people_str = ', '.join([f"{name} ({desc})" for name, desc in list(self.user_info['mentioned_people'].items())[:3]])
            system_prompt += f"\n- People mentioned: {people_str}"
        
        user_prompt = self._build_user_prompt(
            context, emotion, trigger, preference_profile, activity, memory, web_context
        )
        
        # Call cloud LLM
        try:
            response = self._call_llm(system_prompt, user_prompt, has_web_context=bool(web_context))
            
            # Extract and store important information from user's speech
            if context.get('user_speech'):
                self._extract_important_info(context['user_speech'])
            
            # Apply personality adaptation if available
            if preference_profile:
                response = self._apply_personality_adaptation(response, preference_profile)
            
            # Store in conversation history
            self.conversation_history.append({
                'user': context.get('user_speech', ''),
                'assistant': response,
                'trigger': trigger,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep last 20 exchanges (increased from 10)
            if len(self.conversation_history) > 20:
                self.conversation_history.pop(0)
            
            # Track response to avoid repetition
            self.recent_responses.append(response)
            if len(self.recent_responses) > 5:
                self.recent_responses.pop(0)
            
            return {
                'text': response,
                'emotion': emotion['emotion'],
                'trigger': trigger
            }
        except Exception as e:
            print(f"LLM error: {e}")
            return {
                'text': self._fallback_response(trigger, emotion),
                'emotion': emotion['emotion'],
                'trigger': trigger
            }
    
    def _extract_important_info(self, user_speech: str):
        """Extract and store important information from user's speech"""
        speech_lower = user_speech.lower()
        
        # Extract name if mentioned - IMPROVED PATTERNS
        name_patterns = [
            'my name is ',
            "i'm ",
            "i am ",
            'call me ',
            'this is ',
            'name\'s '
        ]
        
        for pattern in name_patterns:
            if pattern in speech_lower:
                # Find the pattern and extract what comes after
                idx = speech_lower.find(pattern)
                after_pattern = user_speech[idx + len(pattern):].strip()
                
                # Extract the first word(s) as name
                words = after_pattern.split()
                if words:
                    # Handle multi-word names (e.g., "Captain Levi")
                    potential_name = []
                    for word in words[:3]:  # Max 3 words for name
                        clean_word = word.strip('.,!?')
                        if clean_word and (clean_word[0].isupper() or clean_word.lower() in ['captain', 'mr', 'mrs', 'ms', 'dr']):
                            potential_name.append(clean_word)
                        else:
                            break
                    
                    if potential_name:
                        full_name = ' '.join(potential_name)
                        self.user_info['name'] = full_name
                        print(f"📝 Learned user's name: {full_name}")
                        
                        # Persist to memory manager
                        if self.memory_manager:
                            self.memory_manager.store_fact('user_name', full_name)
                            self.memory_manager.store_fact('user_info', self.user_info)
                        break
        
        # Extract character/person mentions (capitalized words that aren't common words)
        words = user_speech.split()
        common_words = {'I', 'The', 'A', 'An', 'This', 'That', 'These', 'Those', 'My', 'Your', 'His', 'Her'}
        for i, word in enumerate(words):
            clean_word = word.strip('.,!?')
            if clean_word and clean_word[0].isupper() and clean_word not in common_words and len(clean_word) > 2:
                # Get context (next few words)
                context_words = words[i:min(i+4, len(words))]
                context = ' '.join(context_words)
                self.user_info['mentioned_people'][clean_word] = context[:50]
        
        # Extract interests from keywords
        interest_keywords = ['love', 'like', 'enjoy', 'favorite', 'fan of', 'into']
        for keyword in interest_keywords:
            if keyword in speech_lower:
                # Extract what comes after the keyword
                idx = speech_lower.find(keyword)
                after = user_speech[idx:idx+50]
                if after and after not in self.user_info['interests']:
                    self.user_info['interests'].append(after)
                    
                    # Persist to memory manager
                    if self.memory_manager:
                        self.memory_manager.store_fact('user_info', self.user_info)
    
    def load_user_info(self, memory_manager):
        """Load user info from memory manager"""
        self.memory_manager = memory_manager
        
        # Load user name
        user_name = memory_manager.long_term.get('user_name')
        if user_name:
            self.user_info['name'] = user_name
            print(f"📚 Loaded user's name from memory: {user_name}")
        
        # Load full user info
        stored_user_info = memory_manager.long_term.get('user_info')
        if stored_user_info:
            self.user_info.update(stored_user_info)
            print(f"📚 Loaded user info from memory")
    
    def build_emotion_context(self, emotion: Dict) -> str:
        """Build emotion-specific context for prompt"""
        emotion_name = emotion.get('emotion', 'neutral')
        intensity = emotion.get('intensity', 0.5)
        
        emotion_contexts = {
            'sad': "The user appears sad. Be supportive, empathetic, and offer comfort.",
            'angry': "The user appears angry. Be calm, understanding, and non-confrontational.",
            'happy': "The user appears happy. Be positive, celebratory, and share their joy.",
            'tired': "The user appears tired. Be gentle, brief, and considerate of their energy.",
            'focused': "The user appears focused. Be brief and avoid interrupting their flow.",
            'concerned': "The user may need support. Be caring and attentive.",
            'neutral': "The user appears neutral. Be friendly and natural."
        }
        
        return emotion_contexts.get(emotion_name, emotion_contexts['neutral'])
    
    def _build_user_prompt(self, context, emotion, trigger, preference_profile, activity, memory, web_context=None):
        """Build contextual prompt with enhanced information"""
        prompt_parts = []
        
        # Add web search results if available
        if web_context:
            prompt_parts.append(web_context)
            prompt_parts.append("")
        
        # Add basic context
        prompt_parts.append(f"Current time: {context['time']}")
        prompt_parts.append(f"User present: {context['user_present']}")
        prompt_parts.append(f"Your current emotion: {emotion['emotion']}")
        
        # Add emotion context
        emotion_context = self.build_emotion_context(emotion)
        prompt_parts.append(f"\nEmotion guidance: {emotion_context}")
        
        # Add activity context if available
        if activity:
            prompt_parts.append(f"User activity: {activity}")
        
        # Add relevant memory context
        if memory:
            relevant_memories = memory.get_relevant_context(context, limit=3)
            if relevant_memories:
                prompt_parts.append("\nRelevant past context:")
                for mem in relevant_memories[:2]:  # Limit to 2 to save tokens
                    if 'response' in mem and 'text' in mem['response']:
                        prompt_parts.append(f"- Previously discussed: {mem['response']['text'][:50]}...")
        
        # Add preference-based guidance
        if preference_profile:
            if preference_profile.conversation_style == 'brief':
                prompt_parts.append("\nStyle: Keep response very brief (1-2 sentences max)")
            elif preference_profile.conversation_style == 'detailed':
                prompt_parts.append("\nStyle: Provide detailed, thoughtful response")
            
            if preference_profile.formality_level == 'formal':
                prompt_parts.append("Tone: Use formal, professional language")
            else:
                prompt_parts.append("Tone: Use casual, friendly language")
        
        # Add trigger-specific context
        user_speech = context.get('user_speech', '')
        
        if trigger == 'user_spoke':
            prompt_parts.append(f"\nUser said: \"{user_speech}\"")
            
            # Check if this requires reasoning
            if self.reasoning.requires_reasoning(user_speech):
                question_type = self.reasoning.identify_question_type(user_speech)
                template = self.reasoning.get_reasoning_template(question_type)
                prompt_parts.append(f"\nThis is a {question_type} question. Use this structure:")
                prompt_parts.append(template)
            
            prompt_parts.append("Respond naturally to what they said.")
        elif trigger == 'system_started':
            prompt_parts.append("\nYou just started up. Greet the user warmly and let them know you're ready to chat.")
        elif trigger == 'user_entered':
            prompt_parts.append("\nUser just entered the room. Greet them warmly.")
        elif trigger == 'proactive_idle':
            prompt_parts.append("\nUser has been idle. Start a friendly conversation.")
        elif trigger == 'late_night_concern':
            prompt_parts.append(f"\nIt's {context['time']} and user is still up. Express gentle concern.")
        elif trigger == 'supportive_mood':
            prompt_parts.append(f"\nUser appears {emotion['emotion']}. Offer support and understanding.")
        elif trigger == 'rest_suggestion':
            prompt_parts.append("\nUser appears tired late at night. Gently suggest rest.")
        elif trigger == 'break_suggestion':
            prompt_parts.append("\nUser has been focused for a long time. Suggest taking a break.")
        elif trigger == 'completion_reinforcement':
            prompt_parts.append("\nUser appears to have completed something. Celebrate their achievement.")
        elif trigger == 'return_greeting':
            prompt_parts.append("\nUser returned after being away. Welcome them back.")
        
        return '\n'.join(prompt_parts)
        
        # Add emotion context
        emotion_context = self.build_emotion_context(emotion)
        prompt_parts.append(f"\nEmotion guidance: {emotion_context}")
        
        # Add activity context if available
        if activity:
            prompt_parts.append(f"User activity: {activity}")
        
        # Add relevant memory context
        if memory:
            relevant_memories = memory.get_relevant_context(context, limit=3)
            if relevant_memories:
                prompt_parts.append("\nRelevant past context:")
                for mem in relevant_memories[:2]:  # Limit to 2 to save tokens
                    if 'response' in mem and 'text' in mem['response']:
                        prompt_parts.append(f"- Previously discussed: {mem['response']['text'][:50]}...")
        
        # Add preference-based guidance
        if preference_profile:
            if preference_profile.conversation_style == 'brief':
                prompt_parts.append("\nStyle: Keep response very brief (1-2 sentences max)")
            elif preference_profile.conversation_style == 'detailed':
                prompt_parts.append("\nStyle: Provide detailed, thoughtful response")
            
            if preference_profile.formality_level == 'formal':
                prompt_parts.append("Tone: Use formal, professional language")
            else:
                prompt_parts.append("Tone: Use casual, friendly language")
        
        # Add trigger-specific context
        if trigger == 'user_spoke':
            prompt_parts.append(f"\nUser said: \"{context['user_speech']}\"")
            prompt_parts.append("Respond naturally to what they said.")
        elif trigger == 'system_started':
            prompt_parts.append("\nYou just started up. Greet the user warmly and let them know you're ready to chat.")
        elif trigger == 'user_entered':
            prompt_parts.append("\nUser just entered the room. Greet them warmly.")
        elif trigger == 'proactive_idle':
            prompt_parts.append("\nUser has been idle. Start a friendly conversation.")
        elif trigger == 'late_night_concern':
            prompt_parts.append(f"\nIt's {context['time']} and user is still up. Express gentle concern.")
        elif trigger == 'supportive_mood':
            prompt_parts.append(f"\nUser appears {emotion['emotion']}. Offer support and understanding.")
        elif trigger == 'rest_suggestion':
            prompt_parts.append("\nUser appears tired late at night. Gently suggest rest.")
        elif trigger == 'break_suggestion':
            prompt_parts.append("\nUser has been focused for a long time. Suggest taking a break.")
        elif trigger == 'completion_reinforcement':
            prompt_parts.append("\nUser appears to have completed something. Celebrate their achievement.")
        elif trigger == 'return_greeting':
            prompt_parts.append("\nUser returned after being away. Welcome them back.")
        
        return '\n'.join(prompt_parts)
    
    def _call_llm(self, system_prompt, user_prompt, has_web_context=False):
        """Call LLM API with full conversation history"""
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Build messages array with conversation history
        messages = [{'role': 'system', 'content': system_prompt}]
        
        # Add recent conversation history (reduced from 8 to 4 for faster processing)
        for entry in self.conversation_history[-4:]:
            if entry.get('user'):
                messages.append({'role': 'user', 'content': entry['user']})
            if entry.get('assistant'):
                messages.append({'role': 'assistant', 'content': entry['assistant']})
        
        # Add current user prompt
        messages.append({'role': 'user', 'content': user_prompt})
        
        # Adjust max_tokens based on query type
        max_tokens = 250  # Increased for complete responses
        if has_web_context:
            max_tokens = 500  # Increased for detailed knowledge answers
        
        # Detect if this is a simple/casual query
        user_prompt_lower = user_prompt.lower()
        is_simple_query = any(phrase in user_prompt_lower for phrase in [
            'how are you', 'what\'s up', 'how\'s it going', 'what are you doing',
            'are you okay', 'how do you feel', 'what\'s new', 'tell me about yourself'
        ])
        
        # Select model based on query complexity
        model = self.standard_model  # Default to standard model for quality
        
        # Only use fast model for very simple queries
        if is_simple_query:
            max_tokens = 80
            model = self.fast_model
        
        payload = {
            'model': model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': max_tokens,
            'top_p': 0.9,
            'frequency_penalty': 0.5,  # Increased from 0.3 to reduce repetition more
            'presence_penalty': 0.3,  # Increased from 0.2 to encourage brevity
            'stream': False  # Ensure we're not streaming
        }
        
        try:
            response = requests.post(self.api_endpoint, headers=headers, json=payload, timeout=5)  # Reduced timeout from 8 to 5
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
        except requests.exceptions.HTTPError as e:
            print(f"API Error: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
    
    def _apply_personality_adaptation(self, response: str, preference_profile) -> str:
        """
        Apply personality adaptation to response
        
        Args:
            response: Generated response text
            preference_profile: User's preference profile
            
        Returns:
            Adapted response text
        """
        # For brief style, truncate if too long
        if preference_profile.conversation_style == 'brief':
            sentences = response.split('.')
            if len(sentences) > 2:
                response = '. '.join(sentences[:2]) + '.'
        
        # Note: Formality and other adaptations are handled in prompt
        # This is a post-processing step for length
        
        return response
    
    def select_topics(self, preference_profile, active_strategies: List) -> List[str]:
        """
        Select conversation topics based on preferences and strategies
        
        Args:
            preference_profile: User's preference profile
            active_strategies: List of active adaptation strategies
            
        Returns:
            List of recommended topics
        """
        # Get high-preference topics
        preferred_topics = [
            topic for topic, score in preference_profile.topic_preferences.items()
            if score > 0.6
        ]
        
        # Apply active strategies
        for strategy in active_strategies:
            if strategy.strategy_type == 'change_topic':
                # Remove topics targeted by strategies
                if strategy.target in preferred_topics:
                    preferred_topics.remove(strategy.target)
        
        return preferred_topics
    
    def should_use_topic(self, topic: str) -> bool:
        """
        Check if topic was used recently (avoid repetition)
        
        Args:
            topic: Topic to check
            
        Returns:
            True if topic can be used, False if used recently
        """
        from datetime import datetime, timedelta
        
        # Check if topic used in last 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        
        for recent in self.recent_topics:
            if recent['topic'] == topic and recent['timestamp'] > cutoff:
                return False
        
        return True
    
    def record_topic_use(self, topic: str):
        """Record that a topic was used"""
        from datetime import datetime
        
        self.recent_topics.append({
            'topic': topic,
            'timestamp': datetime.now()
        })
        
        # Keep only last 50 topics
        if len(self.recent_topics) > 50:
            self.recent_topics.pop(0)
    
    def _fallback_response(self, trigger, emotion=None):
        """Fallback responses if API fails"""
        emotion_name = emotion.get('emotion', 'neutral') if emotion else 'neutral'
        
        # Emotion-aware fallbacks
        if emotion_name == 'sad':
            return "I'm here for you if you need to talk."
        elif emotion_name == 'tired':
            return "You look tired. Maybe take a break?"
        elif emotion_name == 'happy':
            return "You seem happy! That's great to see."
        
        # Trigger-based fallbacks
        fallbacks = {
            'system_started': "Hey! I'm KD6, your AI companion. I'm here and ready to chat whenever you need me!",
            'user_entered': "Hey! Good to see you.",
            'proactive_idle': "How's it going?",
            'late_night_concern': "Still up? Don't forget to rest.",
            'user_spoke': "I'm here, but having trouble thinking right now.",
            'supportive_mood': "I'm here if you need anything.",
            'rest_suggestion': "Maybe it's time for a break?",
            'break_suggestion': "You've been working hard. Want to take a break?",
            'completion_reinforcement': "Nice work!",
            'return_greeting': "Welcome back!"
        }
        return fallbacks.get(trigger, "I'm here.")
