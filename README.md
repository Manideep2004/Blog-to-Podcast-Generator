# Blog-to-Podcast-Generator
An AI-powered web application that automatically converts blog posts into engaging audio podcasts using advanced web scraping, text summarization, and text-to-speech technologies.
Features
* One-Click Conversion: Transform any blog URL into professional podcast instantly
* AI-Powered Summarization: GPT-4.1 creates concise, conversational summaries (max 2000 characters)
* Natural Voice Generation: ElevenLabs produces high-quality, multilingual audio
* Web-Based Interface: Clean Streamlit UI requiring no technical setup
* Instant Playback: Listen directly in browser or download WAV files
* Smart Content Processing: Preserves key information while making language casual and friendly Tech Stack
* Frontend: Streamlit
* AI Framework: Agno Agent
* Language Model: OpenAI GPT-4.1
* Text-to-Speech: ElevenLabs API
* Web Scraping: Firecrawl
* Language: Python 3.7+ Quick Start: pip install -r requirements.txt streamlit run main.py Add your API keys for OpenAI, ElevenLabs, and Firecrawl, then start converting blogs to podcasts
How It Works:
1. Input: Paste any blog URL
2. Scrape: Firecrawl extracts clean content
3. Summarize: GPT-4.1 creates podcast-friendly summary
4. Generate: ElevenLabs converts text to natural speech
5. Enjoy: Play or download your new podcast
Requirements:
* Python 3.7+
* OpenAI API key
* ElevenLabs API key
* Firecrawl API key
