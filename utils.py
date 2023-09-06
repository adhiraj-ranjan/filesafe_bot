import firebase_admin
from firebase_admin import credentials, db
from base64 import b64encode, b64decode

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, 
{
    "databaseURL": "https://filesafe-bot-default-rtdb.asia-southeast1.firebasedatabase.app"
})

files = db.reference("files/")


def add_file(key, val):
    files.update({b64encode(key.encode('utf-8')).decode('utf-8'): val})

def get_message_id(key):
    id = files.child(b64encode(key.encode('utf-8')).decode('utf-8')).get()
    return id