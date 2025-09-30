# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Main Application Commands
```bash
# RECOMMENDED: Main execution file for daily automation
run_quiz_bot.bat

# Alternative Python runner (if batch file fails)
python run_quiz_bot.py

# Manual execution of individual components
python core/app.py        # Video generation only
python core/reporter.py   # Analysis and reporting only
```

### File Organization
- **Main execution**: `run_quiz_bot.bat` (PRIMARY - use this)
- **Archive**: Old/test files moved to `archive/` directory
- **Logs**: All execution logs in `logs/` directory

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Activate virtual environment (Windows)
call new_venv\Scripts\activate.bat

# Run with virtual environment
new_venv\Scripts\python.exe core/app.py
```

### Testing
```bash
# Run individual test files
python test_workflow.py
python test_upload.py
python test_app_exit.py
```

## Architecture Overview

This is an **automated Kanji quiz video generation system** that creates, uploads, and analyzes YouTube videos using AI.

### Core Workflow
1. **Script Generation** (`core/app.py`): Uses Gemini AI to generate quiz scripts based on past performance analysis
2. **Video Production** (`core/video_generator.py`): Creates videos using MoviePy with VOICEVOX-generated audio
3. **YouTube Upload** (`handlers/youtube_handler.py`): Automatically uploads videos with metadata
4. **Performance Analysis** (`core/reporter.py`): Analyzes video metrics and generates improvement plans
5. **Data Management** (`handlers/g_sheet_handler.py`): Maintains all data in Google Sheets

### Key Components

**Core Modules:**
- `core/app.py`: Main video generation pipeline controller
- `core/reporter.py`: Analytics and reporting engine  
- `core/video_generator.py`: Video creation using MoviePy
- `core/performance_analyzer.py`: Video performance analysis

**External API Handlers:**
- `handlers/gemini_handler.py`: Gemini AI integration for script generation
- `handlers/voicevox_handler.py`: VOICEVOX text-to-speech integration
- `handlers/youtube_handler.py`: YouTube Data API v3 integration
- `handlers/g_sheet_handler.py`: Google Sheets API integration
- `handlers/discord_handler.py`: Discord webhook notifications
- `handlers/analysis_ai.py`: AI-powered video analysis

### Data Flow
1. Past video data retrieved from Google Sheets
2. AI generates improvement plans and new quiz scripts  
3. VOICEVOX converts script to audio files
4. MoviePy assembles video with background, images, and audio
5. Video uploaded to YouTube via API
6. Performance data tracked back to Google Sheets
7. Discord notifications sent for status updates

### Environment Variables Required
```env
SPREADSHEET_ID="your_google_sheets_id"
GEMINI_API_KEY="your_gemini_api_key" 
DISCORD_WEBHOOK_URL="your_discord_webhook_url"
DISCORD_WEBHOOK_URL_ERROR="your_error_webhook_url"
```

### Authentication Files
- `json/credentials.json`: Google Sheets service account credentials
- `json/client_secret.json`: YouTube API OAuth2 credentials
- `token.pickle`: YouTube API token cache (auto-generated)

### Key Configuration
- `config/prompts.json`: AI prompt templates for script generation and analysis
- VOICEVOX engine path configured in `core/app.py:31`
- Google Sheets structure defined by `EXPECTED_HEADERS` in `g_sheet_handler.py:13`

### Logging
All operations logged to timestamped files in `logs/` directory with structured error handling and Discord notifications for failures.