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

# Middleware to restrict bot access to BOT_ADMINS only
def admin_filter(_, __, message: Message):
    return message.from_user.id in Config.BOT_ADMINS

@Bot.on_message(filters.private & filters.create(admin_filter))
async def user_status_handler(bot: Client, cmd: Message):
    await handle_user_status(bot, cmd)

@Bot.on_message(filters.command("start") & filters.private & filters.create(admin_filter))
async def start(bot: Client, cmd: Message):
    if cmd.from_user.id in Config.BANNED_USERS:
        await cmd.reply_text("🚫 Sorry, you are banned.")
        return
    
    if Config.UPDATES_CHANNEL is not None:
        force_sub_status = await handle_force_sub(bot, cmd)
        if force_sub_status == 400:
            return

    usr_cmd = cmd.text.split("_", 1)[-1]
    if usr_cmd == "/start":
        await add_user_to_database(bot, cmd)
        await cmd.reply_text(
            Config.HOME_TEXT.format(cmd.from_user.first_name, cmd.from_user.id),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Updates", url="https://t.me/+Qi0jCnSsuFkwODA1"),
                 InlineKeyboardButton("💬 Support", url="https://t.me/+HXVFsszfxj81Yjdl")],
                [InlineKeyboardButton("🚪 Close", callback_data="closeMessage")]
            ])
        )
    else:
        try:
            try:
                file_id = int(b64_to_str(usr_cmd).split("_")[-1])
            except (Error, UnicodeDecodeError):
                file_id = int(usr_cmd.split("_")[-1])
            
            GetMessage = await bot.get_messages(chat_id=Config.DB_CHANNEL, message_ids=file_id)
            message_ids = GetMessage.text.split(" ") if GetMessage.text else [int(GetMessage.id)]
            
            _response_msg = await cmd.reply_text(f"📂 **Total Files:** `{len(message_ids)}`", quote=True)

            for msg_id in message_ids:
                await send_media_and_reply(bot, user_id=cmd.from_user.id, file_id=int(msg_id))
        except Exception as err:
            await cmd.reply_text(f"⚠️ **Error:** `{err}`")

@Bot.on_message(filters.command("batch") & filters.private & filters.create(sudo_filter))
async def batch_command(bot: Client, message: Message):
    batch_ids = message.text.split()[1:]  # Get batch file IDs from command
    
    if not batch_ids:
        await message.reply("⚠️ Please provide valid numeric file IDs.")
        return

    valid_batch_ids = []
    for file_id in batch_ids:
        if file_id.isdigit():  # Ensures only numbers are considered
            valid_batch_ids.append(int(file_id))
        else:
            await message.reply(f"⚠️ Invalid file ID: `{file_id}`. Only numbers are allowed.")
            return

    _response_msg = await message.reply_text(f"📂 **Processing {len(valid_batch_ids)} files...**", quote=True)
    
    for file_id in valid_batch_ids:
        try:
            GetMessage = await bot.get_messages(chat_id=Config.DB_CHANNEL, message_ids=file_id)
            if not GetMessage:
                await message.reply(f"⚠️ File `{file_id}` not found in the database.")
                continue
            
            await send_media_and_reply(bot, user_id=message.from_user.id, file_id=GetMessage.id)
        except Exception as err:
            await message.reply_text(f"⚠️ Error processing file `{file_id}`: `{err}`")
    
    await _response_msg.edit(f"✅ Batch Processing Complete! {len(valid_batch_ids)} files sent.")


@Bot.on_message((filters.document | filters.video | filters.audio | filters.photo) & ~filters.chat(Config.DB_CHANNEL) & filters.create(admin_filter))
async def main(bot: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        await add_user_to_database(bot, message)

        if Config.UPDATES_CHANNEL:
            force_sub_status = await handle_force_sub(bot, message)
            if force_sub_status == 400:
                return

        if message.from_user.id in Config.BANNED_USERS:
            await message.reply_text(
                "🚫 Sorry, you are banned!\n\nContact [Support Group](https://t.me/+HXVFsszfxj81Yjdl)",
                disable_web_page_preview=True
            )
            return

        try:
            forwarded_msg = await message.forward(Config.DB_CHANNEL)
            file_er_id = str(forwarded_msg.id)
            share_link = f"https://telegram.me/{Config.BOT_USERNAME}?start=F2Botz_{str_to_b64(file_er_id)}"
            short_link = get_short(share_link)

            await message.reply_text(
                "**✅ Your file is stored!**\n\n"
                f"🔗 Permanent Link: <code>{short_link}</code>\n\n"
                "Click the link to retrieve your file!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🌐 Original Link", url=share_link),
                     InlineKeyboardButton("🔗 Short Link", url=short_link)]
                ]),
                disable_web_page_preview=True, quote=True
            )
        except FloodWait as sl:
            await asyncio.sleep(sl.value)
            await bot.send_message(
                chat_id=int(Config.LOG_CHANNEL),
                text=f"🚨 **FloodWait Alert:** `{sl.value}s` wait triggered from `{message.chat.id}`",
                disable_web_page_preview=True
            )

Bot.run()
