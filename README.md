# KD6 AI Companion

An autonomous AI companion with real-time voice interaction, visual avatar, and proactive behavior. Now with **intelligence enhancements** including emotion detection, preference learning, and self-reflection capabilities.

## ✨ New in Version 2.0: Intelligence Enhancements

KD6 now features advanced intelligence capabilities:

- 🎭 **Enhanced Mood Detection** - Real-time emotion recognition from facial expressions
- 💬 **Proactive Conversations** - Context-aware conversation initiation based on your mood and activity
- 🧠 **Preference Learning** - Adapts to your communication style and topic preferences over time
- 🔄 **Self-Reflection** - Continuously learns from interactions and improves behavior

[Read the Quick Start Guide →](QUICKSTART_INTELLIGENCE.md) | [Full Documentation →](INTELLIGENCE_ENHANCEMENTS.md)

## Architecture
- **Local**: Perception (with emotion detection), context, decision engine (with proactive triggers), memory (with learning), avatar
- **Cloud**: Groq LLM (Llama 3.3 70B) + Local Windows SAPI TTS

## Quick Start

1. **Install dependencies**:
```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt  # For voice input and automation
pip install -r requirements-avatar.txt    # For avatar display
```

2. **Configure API keys** in `config.json`:
```json
{
  "api": {
    "llm_api_key": "your-groq-api-key-here"
  }
}
```

3. **Verify installation**:
```bash
python verify_installation.py
```

4. **Run comprehensive tests**:
```bash
python test_intelligence.py
```

5. **Start KD6**:
```bash
python main.py
```

## Features

### Core Features
- ✅ Real-time webcam presence detection
- ✅ Voice input with speech recognition
- ✅ Natural language conversation (Groq LLM)
- ✅ Text-to-speech output (Windows SAPI)
- ✅ Live2D avatar display (Allium model)
- ✅ Memory system (short-term, long-term, episodic)

### Intelligence Features (v2.0)
- ✅ **Emotion Detection**: Recognizes 7 emotions from facial expressions
- ✅ **Proactive Triggers**: 5 types of context-aware conversation starters
- ✅ **Activity Inference**: Detects when you're working, taking breaks, or completing tasks
- ✅ **Preference Learning**: Learns your topic preferences and communication style
- ✅ **Self-Reflection**: Analyzes conversation effectiveness and adapts strategies
- ✅ **Memory Persistence**: Saves and loads learning data automatically
- ✅ **Privacy-First**: All data stored locally, no cloud storage

### Automation Features (v2.1)
- ✅ **Browser Control**: Open websites, search Google, play YouTube videos
- ✅ **Task Management**: Create to-do lists, set reminders, track tasks
- ✅ **Voice Commands**: Natural language automation ("play Billie Eilish on YouTube")
- ✅ **Smart Reminders**: Time-based notifications with automatic delivery

[Read the Automation Guide →](AUTOMATION_GUIDE.md)

### Knowledge Enhancement (v2.2 - New!)
- ✅ **Web Search Integration**: Automatic internet search for factual questions
- ✅ **Enhanced Reasoning**: Step-by-step thinking for complex topics
- ✅ **Sourced Answers**: Cites sources from web searches
- ✅ **Any Topic**: Ask about anything - current events, how-tos, definitions, facts
- ✅ **Smart Detection**: Automatically knows when to search vs. casual chat

[Read the Knowledge Guide →](KNOWLEDGE_ENHANCEMENT.md)

## Project Structure
- `main.py` - Entry point and main loop with intelligence integration
- `perception/` - Webcam (with emotion detection), mic, presence detection
- `context/` - Context builder and state management
- `memory/` - Memory system with preference learning and reflection
  - `preference_learner.py` - Learns user preferences from interactions
  - `reflection.py` - Self-reflection and adaptation module
- `emotion/` - Emotion engine with history tracking
  - `detector.py` - Facial emotion detection
- `personality/` - Personality layer
- `decision/` - Decision engine with proactive triggers
- `conversation/` - LLM integration with context awareness
- `action/` - TTS and avatar output
- `avatar/` - Visual avatar interface (Live2D)
- `utils/` - Helper functions

## Documentation

- 📖 [Intelligence Enhancements Documentation](INTELLIGENCE_ENHANCEMENTS.md) - Detailed feature descriptions
- 🚀 [Quick Start Guide](QUICKSTART_INTELLIGENCE.md) - Get started with intelligence features
- 🧠 [Knowledge Enhancement Guide](KNOWLEDGE_ENHANCEMENT.md) - Web search and enhanced reasoning
- 🤖 [Automation Guide](AUTOMATION_GUIDE.md) - Voice commands and task management
- 📋 [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - Technical implementation details
- 📝 [Changelog](CHANGELOG_INTELLIGENCE.md) - Version history and changes
- 📚 [Setup Guide](SETUP_GUIDE.md) - Original setup instructions

## Configuration

The `config.json` file now includes intelligence settings:

```json
{
  "emotion_detection": {
    "confidence_threshold": 0.5,
    "smoothing_frames": 3
  },
  "proactive_conversation": {
    "min_interval_seconds": 600,
    "max_daily_proactive": 20
  },
  "learning": {
    "min_interactions_for_patterns": 10,
    "preference_confidence_threshold": 0.6
  },
  "reflection": {
    "idle_reflection_minutes": 30,
    "deep_reflection_hour": 3
  }
}
```

See [INTELLIGENCE_ENHANCEMENTS.md](INTELLIGENCE_ENHANCEMENTS.md) for full configuration options.

## Testing

Run the comprehensive test suite:

```bash
python test_intelligence.py
```

All tests should pass:
- ✅ Emotion detection tests
- ✅ Emotion engine tests
- ✅ Decision engine tests
- ✅ Preference learner tests
- ✅ Reflection module tests
- ✅ Memory persistence tests
- ✅ Integration tests

## Data Management

KD6 stores learning data locally in the `memory/` directory:

```python
from main import KD6Companion

companion = KD6Companion()

# Export learning data
companion.export_data('backup.json')

# Import learning data
companion.import_data('backup.json')

# Clear all learning data
companion.clear_data()
```

## Privacy & Security

- 🔒 All data stored locally (no cloud storage)
- 🔒 No webcam frames saved to disk
- 🔒 Only emotion labels stored (not images)
- 🔒 User-controlled data export/import/clear
- 🔒 UTF-8 encoding for international support

## Requirements

- Python 3.7+
- Webcam (for presence and emotion detection)
- Microphone (for voice input)
- Windows OS (for SAPI TTS)
- Internet connection (for Groq LLM API)

## Troubleshooting

**Emotion detection not working?**
- Check camera permissions
- Verify `camera_index` in config.json
- System falls back to neutral emotion if detection fails

**No proactive conversations?**
- Check `proactive_enabled: true` in config.json
- Verify rate limiting settings
- Ensure user is detected as present

**Preferences not persisting?**
- Check write permissions in `memory/` directory
- Verify UTF-8 encoding support
- Check logs for file I/O errors

See [INTELLIGENCE_ENHANCEMENTS.md](INTELLIGENCE_ENHANCEMENTS.md) for more troubleshooting tips.

## Version History

- **v2.2.0** (Current) - Knowledge Enhancement
  - Web search integration for factual questions
  - Enhanced reasoning with step-by-step thinking
  - Sourced answers with citations
  - Automatic trigger detection for knowledge queries
  - Adaptive response length (casual vs. detailed)

- **v2.1.0** - Automation System
  - Browser control (YouTube, Google, websites)
  - Task management with reminders
  - Natural language voice commands
  - Smart reminder notifications

- **v2.0.0** - Intelligence Enhancements
  - Enhanced mood detection with facial emotion recognition
  - Proactive conversation improvements with 5 trigger types
  - Memory enhancements with preference learning
  - Self-reflection module with adaptation strategies
  
- **v1.0.0** - Initial Release
  - Basic perception, conversation, and avatar features

See [CHANGELOG_INTELLIGENCE.md](CHANGELOG_INTELLIGENCE.md) for detailed version history.

## License

Part of the KD6 AI Companion project.

## Credits

- Emotion Detection: OpenCV + heuristic fallback
- LLM: Groq API (Llama 3.3 70B)
- TTS: Windows SAPI
- Voice Recognition: Google Speech Recognition
- Avatar: Live2D (Allium model)
