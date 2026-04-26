import asyncio
import logging
import os
import sys
import time
from typing import Any, Awaitable, Callable, Dict
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, html, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, TelegramObject
from aiogram.utils.chat_action import ChatActionSender

from database import Database
from gemini_engine import GeminiEngine

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PASSPHRASE = os.getenv("AUTH_PASSPHRASE")
# The SDK supports both, let's try to find either
GEMINI_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# Initialize components
db = Database()
ai = GeminiEngine(api_key=GEMINI_KEY, model_id="gemini-3-flash-preview")

# Middleware to check if user is authorized and log latency
class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        start_time = time.time()
        
        # Allow /start, /auth, /help commands without auth
        is_auth_cmd = False
        if event.text:
            text = event.text.lower()
            if text.startswith(("/start", "/auth", "/help")):
                is_auth_cmd = True

        user_id = event.from_user.id
        is_authorized = db.is_user_authorized(user_id)

        if not is_auth_cmd and not is_authorized:
            await event.answer(f"🔒 You are not authorized to use this bot. Use {html.code('/auth [passphrase]')} to gain access.")
            return

        result = await handler(event, data)
        
        duration = time.time() - start_time
        logging.info(f"Handled message from {user_id} in {duration:.4f}s")
        return result

# Initialize Dispatcher
dp = Dispatcher()
dp.message.outer_middleware(AuthMiddleware())

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}! I'm your AI assistant. Use {html.code('/auth [passphrase]')} if you haven't yet.")

@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    help_text = (
        "Available commands:\n"
        f"{html.code('/start')} - Start the bot\n"
        f"{html.code('/auth [passphrase]')} - Authenticate yourself\n"
        f"{html.code('/reset')} - Clear conversation history\n"
        f"{html.code('/help')} - Show this help message"
    )
    await message.answer(help_text)

@dp.message(Command("auth"))
async def command_auth_handler(message: Message) -> None:
    args = message.text.split()
    if len(args) < 2:
        await message.answer(f"Usage: {html.code('/auth [passphrase]')}")
        return

    user_pass = args[1]
    if user_pass == PASSPHRASE:
        db.authorize_user(message.from_user.id)
        await message.answer("✅ Success! You are now authorized to use the AI.")
    else:
        await message.answer("❌ Incorrect passphrase.")

@dp.message(Command("reset"))
async def command_reset_handler(message: Message) -> None:
    ai.clear_history(message.from_user.id)
    await message.answer("🧹 Conversation history cleared.")

@dp.message()
async def ai_handler(message: Message) -> None:
    """
    Pass the user message to Gemini and return the response with immediate feedback
    """
    if not message.text:
        return

    # Send placeholder message instantly
    placeholder = await message.answer("🤔 Думаю...")

    async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
        response_text = await ai.ask(message.from_user.id, message.text)
        
        # Update the placeholder with the actual response
        try:
            await placeholder.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            # Fallback for malformed markdown or empty responses
            await placeholder.edit_text(response_text, parse_mode=None)

async def main() -> None:
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found.")
        sys.exit(1)

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
