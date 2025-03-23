# (c) @TeleRoidGroup || @PredatorHackerzZ

import os
import asyncio
import traceback
from binascii import Error
from pyrogram import Client, enums, filters
from pyrogram.errors import UserNotParticipant, FloodWait, QueryIdInvalid
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from configs import Config
from handlers.database import db
from handlers.add_user_to_db import add_user_to_database
from handlers.send_file import send_media_and_reply
from handlers.helpers import b64_to_str, str_to_b64
from handlers.check_user_status import handle_user_status
from handlers.force_sub_handler import handle_force_sub, get_invite_link
from handlers.broadcast_handlers import main_broadcast_handler
from handlers.save_media import get_short

# Dictionary to store media lists
MediaList = {}

# Initialize Pyrogram Bot
Bot = Client(
    name=Config.BOT_USERNAME,
    in_memory=True,
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)

# Middleware to restrict bot access to SUDO_USERS and OWNER only
def sudo_filter(_, __, message: Message):
    return message.from_user.id in Config.SUDO_USERS or message.from_user.id == Config.BOT_OWNER

@Bot.on_message(filters.command("all_batches") & filters.private & filters.create(sudo_filter))
async def all_batches(bot: Client, message: Message):
    try:
        all_messages = await bot.get_chat_history(Config.DB_CHANNEL, limit=1000)
        batch_files = [str(msg.id) for msg in all_messages]
        if not batch_files:
            await message.reply("⚠️ No batch files found!")
            return
        batch_text = "\n".join(batch_files)
        await message.reply(f"📂 **All Batch Files:**\n```
{batch_text}
```", quote=True)
    except Exception as err:
        await message.reply(f"⚠️ Error fetching batch files: `{err}`")
