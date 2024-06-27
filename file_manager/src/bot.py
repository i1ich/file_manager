#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

import logging
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    if 'history' not in context.user_data:
        context.user_data['history'] = []
    context.user_data['history'].append(('/start', None))
    await update.message.reply_html(
        rf"Hello, {user.mention_html()}! I'm a bot that can help you with file uploads. "
        "Use the /touch command to start. "
        "Use /history to view the history of commands and file names, "
        "or /history full for a complete history with file sending.",
        reply_markup=ForceReply(selective=True),
    )


async def touch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the user to upload a file and then display its name."""
    if 'history' not in context.user_data:
        context.user_data['history'] = []
    context.user_data['history'].append(('/touch', None))
    await update.message.reply_text("Please upload a file.")
    context.user_data['waiting_for_file'] = True


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the uploaded file."""
    if context.user_data.get('waiting_for_file'):
        file = update.message.document
        if file:
            if 'history' not in context.user_data:
                context.user_data['history'] = []
            file_obj = await file.get_file()
            context.user_data['history'].append((None, (file.file_name, file_obj)))
            await update.message.reply_text(f"File '{file.file_name}' successfully uploaded.")
        else:
            await update.message.reply_text("Please upload a file (not a photo or video).")
        context.user_data['waiting_for_file'] = False
    else:
        await update.message.reply_text("Use the /touch command to upload a file.")


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the history of commands and uploaded files."""
    if 'history' not in context.user_data:
        context.user_data['history'] = []

    full_history = False
    command_args = context.args
    if command_args and command_args[0].lower() == 'full':
        full_history = True
        context.user_data['history'].append(('/history full', None))
    else:
        context.user_data['history'].append(('/history', None))

    history = context.user_data['history']
    if not history:
        await update.message.reply_text("History is empty.")
    else:
        history_text = "Command and file history:\n"
        for item in history:
            if item[0]:  # This is a command
                history_text += f"Command: {item[0]}\n"
            elif item[1]:  # This is a file
                file_name, file_obj = item[1]
                history_text += f"Uploaded file: {file_name}\n"
                if full_history:
                    try:
                        await update.message.reply_document(file_obj)
                    except Exception as e:
                        await update.message.reply_text(f"Failed to send file {file_name}: {str(e)}")

        await update.message.reply_text(history_text)


def main() -> None:
    """Start the bot."""
    application = Application.builder().token("7482872404:AAFjK42XWPajU_VGu71vTBkTt8rqQCGdArk").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("touch", touch))
    application.add_handler(CommandHandler("history", history))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()