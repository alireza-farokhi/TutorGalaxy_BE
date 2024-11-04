from tinydb import TinyDB
from tinydb.storages import Storage
from dotenv import load_dotenv
import os
import yaml
import logging

# Custom YAML Storage class
class YAMLStorage(Storage):
    def __init__(self, filename):
        self.filename = filename
        
    def read(self):
        if not os.path.exists(self.filename):
            return {}
        with open(self.filename, 'r') as f:
            try:
                data = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                return {}
        return data

    def write(self, data):
        with open(self.filename, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
            
    def close(self):
        pass

logger = logging.getLogger(__name__)

# Check if db.yml exists, if not, create it
if not os.path.exists('db.yml'):
    logger.info("db.yml not found, creating a new one.")
    db = TinyDB('db.yml', storage=YAMLStorage)
    
    # Initialize tables
    user_table = db.table('users')
    conversations_table = db.table('conversations')
    topics_table = db.table('topics')
    message_table = db.table('messages')
    asset_table = db.table('assets')
    
    # Optionally, insert initial data or structure
    user_table.insert({'_init': True})
    conversations_table.insert({'_init': True})
    topics_table.insert({'_init': True})
    message_table.insert({'_init': True})
    asset_table.insert({'_init': True})
    
    # Remove the initial documents
    for table in [user_table, conversations_table, topics_table, message_table, asset_table]:
        table.remove(doc_ids=[1])
else:
    # If db.yml exists, just connect to it
    db = TinyDB('db.yml', storage=YAMLStorage)
    user_table = db.table('users')
    conversations_table = db.table('conversations')
    topics_table = db.table('topics')
    message_table = db.table('messages')
    asset_table = db.table('assets')

# Verify tables are initialized
logger.info(f"Database tables: {db.tables()}")
for table_name in db.tables():
    logger.info(f"Table {table_name} has {len(db.table(table_name))} documents")

# Params 
model_engine = 'gpt-4o-mini'
conversation_model = 'gpt-4o-mini'
extraction_model = 'gpt-4o-mini' 
maximum_chat_messages_without_login = 10
max_topic_messages_WO_sub = 50
max_topic_topics_WO_sub = 8
message_per_page = 10

# API_KEYS
load_dotenv()
API_KEYS = os.getenv("OPENAI_API_KEYS", "").split(',')  # Added default empty string