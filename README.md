# Goal
Develop a Telegram bot that provides an interface to interact with Gemini AI, featuring tool-use capabilities for accessing and managing a freeform database.

## Requirements
- **Telegram Interface**: Built using `aiogram` (v3.x) for a modern, asynchronous bot experience.
- **AI Integration**: Powered by the `google-genai` SDK to utilize Gemini's latest models (e.g., `gemini-2.0-flash`).
- **Tool-Use (Function Calling)**: The AI must be able to call specific functions to interact with external data or perform actions.
- **Freeform Database**: A flexible storage system (initially SQLite or local JSON) where the AI can save and retrieve arbitrary information.
- **Context Management**: Support for multi-turn conversations by maintaining chat history.

## Technical Stack
- **Language**: Python 3.10+
- **Bot Framework**: `aiogram`
- **AI SDK**: `google-genai`
- **Storage**: SQLite (for freeform data and session state)
- **Configuration**: `python-dotenv` for environment variable management

## Implementation Plan

### Phase 1: Setup and Basic Bot
1. Initialize the project and install core dependencies.
2. Configure environment variables (`TELEGRAM_BOT_TOKEN`, `GOOGLE_API_KEY`).
3. Create a basic `aiogram` bot with `/start` and `/help` commands.

### Phase 2: AI Engine Integration
1. Implement a `GeminiEngine` class using `google-genai`.
2. Set up basic text generation and conversation history handling.
3. Integrate the engine with the Telegram bot handlers.

### Phase 3: Tool-Use & Database
1. Design the "Freeform Database" schema and interface.
2. Implement tool functions (e.g., `store_information`, `query_information`).
3. Register tools with the Gemini model using function calling.
4. Enable automatic or manual function calling loop to handle AI requests.

### Phase 4: Refinement and UX
1. Add typing indicators and error handling for better user experience.
2. Implement session-based chat history persistence.
3. Final testing of tool-use scenarios (e.g., "Remember that my favorite color is blue" -> "What is my favorite color?").
