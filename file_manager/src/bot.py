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


class Directory:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.subdirectories = {}
        self.files = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    if 'file_system' not in context.user_data:
        context.user_data['file_system'] = Directory('/')
        context.user_data['current_directory'] = context.user_data['file_system']
    await update.message.reply_html(
        rf"Hello, {user.mention_html()}! I'm a bot that simulates a file system. "
        "Available commands:\n"
        "/md &lt;name&gt; - Create a new directory\n"
        "/cd &lt;path&gt; - Change current directory\n"
        "/ls - List files and directories in current directory\n"
        "/touch - Upload a file to current directory",
        reply_markup=ForceReply(selective=True),
    )


async def make_directory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a new directory."""
    if not context.args:
        await update.message.reply_text("Please specify a directory name.")
        return
    dir_name = context.args[0]
    current_dir = context.user_data['current_directory']
    if dir_name in current_dir.subdirectories:
        await update.message.reply_text(f"Directory '{dir_name}' already exists.")
    else:
        new_dir = Directory(dir_name, current_dir)
        current_dir.subdirectories[dir_name] = new_dir
        await update.message.reply_text(f"Directory '{dir_name}' created.")


async def change_directory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Change the current directory."""
    if not context.args:
        await update.message.reply_text("Please specify a directory path.")
        return
    path = context.args[0]
    current_dir = context.user_data['current_directory']
    if path == '../':
        if current_dir.parent:
            context.user_data['current_directory'] = current_dir.parent
            await update.message.reply_text(f"Changed to parent directory: {current_dir.parent.name}")
        else:
            await update.message.reply_text("Already in root directory.")
    elif path in current_dir.subdirectories:
        context.user_data['current_directory'] = current_dir.subdirectories[path]
        await update.message.reply_text(f"Changed to directory: {path}")
    else:
        await update.message.reply_text(f"Directory '{path}' not found.")


async def list_directory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List files and directories in the current directory."""
    current_dir = context.user_data['current_directory']
    content = "Current directory contents:\n"
    for subdir in current_dir.subdirectories:
        content += f"📁 {subdir}\n"
    for file in current_dir.files:
        content += f"📄 {file}\n"
    if not current_dir.subdirectories and not current_dir.files:
        content += "Directory is empty."
    await update.message.reply_text(content)


async def touch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the user to upload a file to the current directory."""
    await update.message.reply_text("Please upload a file.")
    context.user_data['waiting_for_file'] = True


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the uploaded file."""
    if context.user_data.get('waiting_for_file'):
        file = update.message.document
        if file:
            current_dir = context.user_data['current_directory']
            current_dir.files[file.file_name] = file.file_id
            await update.message.reply_text(f"File '{file.file_name}' successfully uploaded to the current directory.")
        else:
            await update.message.reply_text("Please upload a file (not a photo or video).")
        context.user_data['waiting_for_file'] = False
    else:
        await update.message.reply_text("Use the /touch command to upload a file.")


def main() -> None:
    """Start the bot."""
    application = Application.builder().token("7482872404:AAFjK42XWPajU_VGu71vTBkTt8rqQCGdArk").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("md", make_directory))
    application.add_handler(CommandHandler("cd", change_directory))
    application.add_handler(CommandHandler("ls", list_directory))
    application.add_handler(CommandHandler("touch", touch))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()