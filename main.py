from telegram.ext import filters, MessageHandler, CommandHandler, Application, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
import utils
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
import os

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

TOKEN = os.getenv('TOKEN')
CHANNEL_CHAT_ID = -1001982682215

CHANNEL_USERNAME = "@truebotsc"

# Define conversation states

USER_PHRASE_SET, USER_PASSWORD_SET = range(2)
USER_PHRASE_GET, USER_PASSWORD_GET = range(2)

async def start(update, context):
    await update.message.reply_text("Send any file, and specify a secret phrase and password for the file, and access the file anytime later.",
                                     reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="Retrieve File")]], resize_keyboard=True))


async def file_received(update, context):

    if not update.message:
        return
    user_member = await context.bot.get_chat_member(
        chat_id=CHANNEL_USERNAME, user_id=update.message.from_user.id)

    if user_member.status == "member" or user_member.status == "administrator" or user_member.status == "creator":
        pass
    else:
        await update.message.reply_text(
            f"Join TrueBots [💀] {CHANNEL_USERNAME} to use the bot and to Explore more useful bots"
        )
        return

    set_phrase = InlineKeyboardButton(text="Set Phrase & Password", callback_data=update.message.message_id)

    await update.message.reply_text("Set a Memorable Phrase and Password for the file, to retrieve your file later.", reply_markup=InlineKeyboardMarkup([[set_phrase]]), reply_to_message_id=update.message.message_id)
    #await update.message.forward(CHANNEL_CHAT_ID)

async def random_text(update, context):
    await update.message.reply_text("unknown command")


async def phrase_handler(update, context):
    query = update.callback_query
    context.user_data['ids'] = [query.data, query.message.message_id]
    await query.message.reply_text("→ ENTER A PHRASE TO REMEMBER THE FILE ←", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="/cancel")]], resize_keyboard=True))
    return USER_PHRASE_SET


async def handle_phrase(update, context):
    context.user_data['phrase'] = update.message.text
    await update.message.reply_text("🔒 ENTER A PASSWORD 🔒")
    return USER_PASSWORD_SET

async def handle_password(update, context):
    
    f_msg = await context.bot.forward_message(CHANNEL_CHAT_ID, update.message.chat.id, context.user_data['ids'][0])
    utils.add_file(f"{context.user_data['phrase']}:{update.message.text}", f_msg.message_id)

    await update.message.reply_text("File Saved !", reply_to_message_id=context.user_data['ids'][0], reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="Retrieve File")]], resize_keyboard=True))
    
    # End the conversation
    context.user_data.clear()
    return ConversationHandler.END


async def get_handler(update, context):
    await update.message.reply_text("→ ENTER THE PHRASE OF THE FILE ←",
                                     reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="/cancel")]],
                                     resize_keyboard=True))
    return USER_PHRASE_GET


async def get_phrase(update, context):
    context.user_data['phrase'] = update.message.text
    await update.message.reply_text("🔒 ENTER THE PASSWORD 🔒")
    return USER_PASSWORD_GET

async def get_password(update, context):
    
    await update.message.reply_text("Checking... ✅", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="Retrieve File")]], resize_keyboard=True))
    req_file_id = utils.get_message_id(f"{context.user_data['phrase']}:{update.message.text}")
    if req_file_id:
        await context.bot.forward_message(update.message.chat.id, CHANNEL_CHAT_ID, req_file_id)
    else:
        await update.message.reply_text("FILE_NOT_FOUND ❌")
    
    # End the conversation
    context.user_data.clear()

    return ConversationHandler.END

async def end_convo(update, context):
    context.user_data.clear()

    await update.message.reply_text("Process Cancelled ✅", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="Retrieve File")]], resize_keyboard=True))
    
    return ConversationHandler.END


# Log errors
async def error(update, context):
    #if update:
    await update.message.reply_text(str(context.error))
    print(context.error)


# Run the program
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start))

    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.AUDIO | filters.VIDEO, file_received))

    # Create a ConversationHandler to manage the flow
    set_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(phrase_handler, pattern="^\d+$")],
        states={
            USER_PHRASE_SET: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phrase)],
            USER_PASSWORD_SET: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)],
        },
        fallbacks=[CommandHandler('cancel', end_convo)],
    )

    get_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("Retrieve File"), get_handler)],
        states={
            USER_PHRASE_GET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phrase)],
            USER_PASSWORD_GET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler('cancel', end_convo)],
    )
    # Add the ConversationHandler to the dispatcher
    app.add_handler(set_conv_handler)
    app.add_handler(get_conv_handler)

    app.add_handler(MessageHandler(filters.TEXT, random_text))
    # Log all errors
    app.add_error_handler(error)

    app.run_polling()
