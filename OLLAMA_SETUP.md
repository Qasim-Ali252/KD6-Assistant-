# Ollama Local LLM Setup for KD6

## Why Ollama?
- **Ultra-fast responses**: <1 second (vs 3-5 seconds with Groq)
- **No internet required**: Works offline
- **Free**: No API costs
- **Privacy**: All data stays on your machine

## Installation Steps

### 1. Download and Install Ollama
Visit: https://ollama.com/download
- Download Ollama for Windows
- Run the installer
- Ollama will start automatically

### 2. Install a Fast Model
Open Command Prompt or PowerShell and run:

```bash
# Option 1: Llama 3.2 1B (FASTEST - recommended for real-time chat)
ollama pull llama3.2:1b

# Option 2: Phi-3 Mini (Good balance of speed and quality)
ollama pull phi3:mini

# Option 3: Llama 3.2 3B (Better quality, still fast)
ollama pull llama3.2:3b
```

### 3. Test Ollama
```bash
ollama run llama3.2:1b "Hello, how are you?"
```

You should get a response in under 1 second!

### 4. Update KD6 Configuration
The code has been updated to support Ollama. Just change your config.json:

```json
{
  "api": {
    "llm_provider": "ollama",
    "llm_endpoint": "http://localhost:11434/api/generate",
    "ollama_model": "llama3.2:1b",
    "fast_model": "llama3.2:1b",
    "standard_model": "llama3.2:3b"
  }
}
```

### 5. Restart KD6
```bash
python main.py
```

## Model Comparison

| Model | Speed | Quality | Size | Best For |
|-------|-------|---------|------|----------|
| llama3.2:1b | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | 1.3GB | Real-time chat |
| phi3:mini | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | 2.3GB | Balanced |
| llama3.2:3b | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 2.0GB | Quality responses |

## Troubleshooting

**Ollama not responding?**
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
# Close Ollama from system tray and restart it
```

**Model not found?**
```bash
# List installed models
ollama list

# Pull the model again
ollama pull llama3.2:1b
```

## Performance Tips

1. **First response is slower**: Ollama loads the model on first use (~2-3 seconds)
2. **Keep Ollama running**: Subsequent responses are instant
3. **Use 1B model for chat**: Save 3B for complex questions
4. **GPU acceleration**: If you have NVIDIA GPU, Ollama will use it automatically

## Switching Back to Groq

If you want to switch back to Groq:
```json
{
  "api": {
    "llm_provider": "groq",
    "llm_endpoint": "https://api.groq.com/openai/v1/chat/completions",
    "llm_api_key": "your_groq_key"
  }
}
```
