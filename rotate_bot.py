from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters
import ffmpeg
import os

bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    raise ValueError("BOT_TOKEN environment variable not set")

user_videos = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a video and choose rotation angle.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    file = await update.message.video.get_file()
    input_path = f"{user_id}_input.mp4"
    await file.download_to_drive(input_path)
    user_videos[user_id] = input_path

    keyboard = [
        [InlineKeyboardButton("↻ 90°", callback_data="rotate_90"),
         InlineKeyboardButton("↺ 270°", callback_data="rotate_270")],
        [InlineKeyboardButton("🔄 180°", callback_data="rotate_180")]
    ]

    await update.message.reply_text("Choose rotation angle:",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def rotate_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_videos:
        await query.edit_message_text("Send a video first.")
        return

    input_path = user_videos[user_id]
    output_path = f"{user_id}_output.mp4"

    angle = int(query.data.split("_")[1])

    # ffmpeg rotation
    transpose_map = {90: 1, 180: 2, 270: 3}  # ffmpeg transpose codes
    if angle == 180:
        ffmpeg.input(input_path).hflip().vflip().output(output_path).run(overwrite_output=True)
    else:
        ffmpeg.input(input_path).transpose(transpose_map[angle]).output(output_path).run(overwrite_output=True)

    await query.message.reply_video(video=open(output_path, "rb"))

    os.remove(output_path)

async def main():
    import os
    bot_token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(CallbackQueryHandler(rotate_video, pattern="rotate_"))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()  # allows running nested event loops
    asyncio.get_event_loop().run_until_complete(main())


