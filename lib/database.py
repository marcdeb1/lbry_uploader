import tinydb
from settings import DATABASE_NAME, CHANNEL_NAME

class Database:
    db = None
    table = None
    name = ""

    def __init__(self, name=DATABASE_NAME):
        url = "sqlite:///" + name
        self.db = dataset.connect(url)
        self.table = self.db['content']

    def store_item(self, data):
        return self.table.insert(data)

    def get_item(self, identifier):
        return self.table.find_one(identifier=identifier)

    def update_published(self, identifier):
        return self.table.update(dict(identifier=identifier, channel_name=CHANNEL_NAME, published=True), ['identifier'])
