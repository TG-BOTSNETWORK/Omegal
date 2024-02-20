import random
from pyrogram import Client as Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import time 

api_id = "22363963"
api_hash = "5c096f7e8fd4c38c035d53dc5a85d768"
bot_token = "7154920882:AAE2iUvz9UBVx_TsWVNh2IgMA26JCMK2JoY"

app = Client("OmegleBot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

mongo_client = MongoClient("mongodb+srv://Amala203145:Amala2031456@cluster0.t9ibfge.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["omegle_bot"]
users_collection = db["users"]

last_active_times = {}

active_chats = {}

def is_user_online(user_id):
    return user_id in last_active_times and (time.time() - last_active_times[user_id]) < 300  

@app.on_message(filters.command("start"))
def start_command(client, message):
    try:
        user_id = message.chat.id
        user = users_collection.find_one({"_id": user_id})
        if not user:
            users_collection.insert_one({"_id": user_id})
        start_text = "Welcome to Omegle Bot! Start a chat or check your info."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Start Chat", callback_data="start_chat")],
                                         [InlineKeyboardButton("Your Info", callback_data="info")]])
        message.reply_text(start_text, reply_markup=keyboard)
    except Exception as e:
        print("Error:", e)

@app.on_callback_query()
def callback_handler(client, query):
    user_id = query.message.chat.id
    if query.data == "start_chat":
        random_user = users_collection.aggregate([{ "$sample": { "size": 1 } }])
        for user in random_user:
            if user["_id"] != user_id and is_user_online(user["_id"]):
                chat_text = f"You are now chatting with user Stranger. Say hi!"
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Leave Chat", callback_data="leave_chat")]])
                query.message.reply_text(chat_text, reply_markup=keyboard)
                active_chats[user_id] = user['_id']
                active_chats[user['_id']] = user_id
                break
    elif query.data == "info":
        query.message.reply_text(f"Your user ID: {user_id}")
    elif query.data == "leave_chat":
        leave_chat(client, query.message)

@app.on_message(filters.text & ~filters.command("start"))
def chat_handler(client, message):
    user_id = message.chat.id
    # Check if user is in an active chat
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Leave Chat", callback_data="leave_chat")]])
    if user_id in active_chats:
        receiver_id = active_chats[user_id]
        app.send_message(receiver_id, message.text, reply_markup=keyboard)
        # Update last active time of both users
        last_active_times[user_id] = time.time()
        last_active_times[receiver_id] = time.time()

@app.on_message(filters.media & ~filters.command("start"))
def media_handler(client, message):
    user_id = message.chat.id
    # Check if user is in an active chat
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Leave Chat", callback_data="leave_chat")]])
    if user_id in active_chats:
        receiver_id = active_chats[user_id]
        app.forward_messages(receiver_id, user_id, message.id)
        # Update last active time of both users
        last_active_times[user_id] = time.time()
        last_active_times[receiver_id] = time.time()

@app.on_message(filters.command("leave"))
def leave_command(client, message):
    user_id = message.chat.id
    # Check if user is in an active chat
    if user_id in active_chats:
        leave_chat(client, message)
    else:
        message.reply_text("You are not in an active chat.")

def leave_chat(client, message):
    user_id = message.chat.id
    other_user_id = active_chats[user_id]
    del active_chats[user_id]
    del active_chats[other_user_id]
    message.reply_text("You have left the chat.")
    app.send_message(other_user_id, "The other user has left the chat.")

print("Bot Started!")
app.run()
