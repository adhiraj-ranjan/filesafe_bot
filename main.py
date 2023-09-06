from telegram.ext import filters, MessageHandler, CommandHandler, Application, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
import utils

TOKEN = "6422247925:AAHQ-TGNUfFXG1MsaJGMAAfbn0vuaDmw5D4"
CHANNEL_CHAT_ID = -1001982682215


# Define conversation states
USER_PHRASE_SET, USER_PASSWORD_SET = range(2)
USER_PHRASE_GET, USER_PASSWORD_GET = range(2)

async def start(update, context):
    p = KeyboardButton(text="Retrieve File")
    await update.message.reply_text("Send any file, and specify its a secret phrase and password, for the file, and access the file anytime later.", reply_markup=ReplyKeyboardMarkup([[p]]))


async def file_received(update, context):

    if not update.message:
        return

    set_phrase = InlineKeyboardButton(text="Set Phrase & Password", callback_data=update.message.message_id)

    await update.message.reply_text("Set a Memorable Phrase and Password for the file, to retrive your file later.", reply_markup=InlineKeyboardMarkup([[set_phrase]]), reply_to_message_id=update.message.message_id)
    #await update.message.forward(CHANNEL_CHAT_ID)

async def random_text(update, context):
    await update.message.reply_text("not found")


async def phrase_handler(update, context):
    query = update.callback_query
    context.user_data['ids'] = [query.data, query.message.message_id]
    await query.message.reply_text("→ ENTER A PHRASE TO REMEMBER THE FILE ←")
    return USER_PHRASE_SET


async def handle_phrase(update, context):
    context.user_data['phrase'] = update.message.text
    await update.message.reply_text("🔒 ENTER A PASSWORD 🔒")
    return USER_PASSWORD_SET

async def handle_password(update, context):
    
    f_msg = await context.bot.forward_message(CHANNEL_CHAT_ID, update.message.chat.id, context.user_data['ids'][0])
    utils.add_file(f"{context.user_data['phrase']}:{update.message.text}", f_msg.message_id)

    await update.message.reply_text("File Saved !", reply_to_message_id=context.user_data['ids'][0])
    
    # End the conversation
    context.user_data.clear()
    return ConversationHandler.END


async def get_handler(update, context):
    await update.message.reply_text("→ ENTER THE PHRASE OF THE FILE ←")
    return USER_PHRASE_GET


async def get_phrase(update, context):
    context.user_data['phrase'] = update.message.text
    await update.message.reply_text("🔒 ENTER THE PASSWORD 🔒")
    return USER_PASSWORD_GET

async def get_password(update, context):
    
    req_file_id = utils.get_message_id(f"{context.user_data['phrase']}:{update.message.text}")
    if req_file_id:
        await context.bot.forward_message(update.message.chat.id, CHANNEL_CHAT_ID, req_file_id)
    else:
        await update.message.reply_text("FILE_NOT_FOUND_ERROR - phrase or password is incorrect")
    
    # End the conversation
    context.user_data.clear()
    return ConversationHandler.END


# Log errors
async def error(update, context):
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
        entry_points=[CallbackQueryHandler(phrase_handler)],
        states={
            USER_PHRASE_SET: [MessageHandler(filters.TEXT, handle_phrase)],
            USER_PASSWORD_SET: [MessageHandler(filters.TEXT, handle_password)],
        },
        fallbacks=[],
    )

    get_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("Retrieve File"), get_handler)],
        states={
            USER_PHRASE_GET: [MessageHandler(filters.TEXT, get_phrase)],
            USER_PASSWORD_GET: [MessageHandler(filters.TEXT, get_password)],
        },
        fallbacks=[],
    )

    # Add the ConversationHandler to the dispatcher
    app.add_handler(set_conv_handler)
    app.add_handler(get_conv_handler)

    app.add_handler(MessageHandler(filters.TEXT, random_text))
    # Log all errors
    app.add_error_handler(error)

    app.run_polling()
