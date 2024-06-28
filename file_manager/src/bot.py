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
        "/touch - Upload a file to current directory\n"
        "/get &lt;filename&gt; - Get a file from current directory\n"
        "/del &lt;name&gt; - Delete a file or directory\n"
        "/rename &lt;old_name&gt; &lt;new_name&gt; - Rename a file or directory",
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


async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get a file from the current directory."""
    if not context.args:
        await update.message.reply_text("Please specify a file name.")
        return
    file_name = context.args[0]
    current_dir = context.user_data['current_directory']
    if file_name in current_dir.files:
        file_id = current_dir.files[file_name]
        try:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=file_id)
        except Exception as e:
            await update.message.reply_text(f"Failed to send file {file_name}: {str(e)}")
    else:
        await update.message.reply_text(f"File '{file_name}' not found in the current directory.")


async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a file or directory from the current directory."""
    if not context.args:
        await update.message.reply_text("Please specify a file or directory name.")
        return
    item_name = context.args[0]
    current_dir = context.user_data['current_directory']
    if item_name in current_dir.files:
        del current_dir.files[item_name]
        await update.message.reply_text(f"File '{item_name}' has been deleted.")
    elif item_name in current_dir.subdirectories:
        del current_dir.subdirectories[item_name]
        await update.message.reply_text(f"Directory '{item_name}' and its contents have been deleted.")
    else:
        await update.message.reply_text(f"'{item_name}' not found in the current directory.")


async def rename_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Rename a file or directory in the current directory."""
    if len(context.args) != 2:
        await update.message.reply_text("Please specify both old and new names.")
        return
    old_name, new_name = context.args
    current_dir = context.user_data['current_directory']
    if old_name in current_dir.files:
        current_dir.files[new_name] = current_dir.files.pop(old_name)
        await update.message.reply_text(f"File '{old_name}' has been renamed to '{new_name}'.")
    elif old_name in current_dir.subdirectories:
        current_dir.subdirectories[new_name] = current_dir.subdirectories.pop(old_name)
        current_dir.subdirectories[new_name].name = new_name
        await update.message.reply_text(f"Directory '{old_name}' has been renamed to '{new_name}'.")
    else:
        await update.message.reply_text(f"'{old_name}' not found in the current directory.")


def main() -> None:
    """Start the bot."""
    application = Application.builder().token("7482872404:AAFjK42XWPajU_VGu71vTBkTt8rqQCGdArk").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("md", make_directory))
    application.add_handler(CommandHandler("cd", change_directory))
    application.add_handler(CommandHandler("ls", list_directory))
    application.add_handler(CommandHandler("touch", touch))
    application.add_handler(CommandHandler("get", get_file))
    application.add_handler(CommandHandler("del", delete_item))
    application.add_handler(CommandHandler("rename", rename_item))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()