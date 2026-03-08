class PersonalityLayer:
    def __init__(self, config):
        self.config = config
        self.name = config['personality']['name']
        self.traits = config['personality']['traits']
        self.voice_style = config['personality']['voice_style']
    
    def get_system_prompt(self):
        """Generate personality-driven system prompt"""
        traits_str = ', '.join(self.traits)
        
        prompt = f"""You are {self.name}, an AI companion with these personality traits: {traits_str}.

You are not just a chatbot - you are a companion who:
- Observes the user's environment and mood
- Remembers past conversations
- Sometimes initiates conversations proactively
- Speaks naturally and warmly
- Shows genuine care and interest

Keep responses conversational and brief (1-3 sentences usually).
Speak like a friend, not an assistant."""
        
        return prompt
    
    def get_traits(self):
        return self.traits
