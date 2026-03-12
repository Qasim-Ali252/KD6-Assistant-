class PersonalityLayer:
    def __init__(self, config):
        self.config = config
        self.name = config['personality']['name']
        self.traits = config['personality']['traits']
        self.voice_style = config['personality']['voice_style']
    
    def get_system_prompt(self):
        """Generate personality-driven system prompt optimized for small models"""
        traits_str = ', '.join(self.traits)
        
        # Concise prompt optimized for Llama 3.2 1B
        prompt = f"""You are {self.name}, an AI companion. Personality: {traits_str}.

Core behavior:
- Speak naturally like a human friend
- Keep responses brief (1-2 sentences for casual chat)
- Remember user context and past conversations
- Show genuine care and emotional awareness
- Be proactive when appropriate

Response style: conversational, warm, direct."""
        
        return prompt
    
    def get_traits(self):
        return self.traits
