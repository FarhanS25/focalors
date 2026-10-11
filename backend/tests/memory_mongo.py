"""In-memory stand-in for the MongoDB calls this app uses. Not Atlas."""

import copy
from datetime import datetime, timezone

from bson import ObjectId


class InsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class MemoryCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, key_or_list, direction=None):
        if isinstance(key_or_list, list):
            key, direction = key_or_list[0]
        else:
            key = key_or_list
        reverse = int(direction) < 0

        def sort_value(document):
            value = document.get(key)
            return value if value is not None else datetime.min.replace(tzinfo=timezone.utc)

        self.documents.sort(key=sort_value, reverse=reverse)
        return self

    def limit(self, count):
        self.documents = self.documents[: int(count)]
        return self

    def __iter__(self):
        return iter(self.documents)


class MemoryCollection:
    def __init__(self):
        self.documents = []
        self.indexes = []

    def create_index(self, keys, name=None):
        self.indexes.append(name or str(keys))
        return name or str(keys)

    def insert_one(self, document):
        stored = copy.deepcopy(document)
        stored["_id"] = ObjectId()
        self.documents.append(stored)
        return InsertResult(stored["_id"])

    def find(self, *args, **kwargs):
        return MemoryCursor(copy.deepcopy(self.documents))


class MemoryDatabase:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MemoryCollection()
        return self.collections[name]


class MemoryAdmin:
    def command(self, name, *args, **kwargs):
        if name != "ping":
            raise RuntimeError(f"Unsupported command {name}")
        return {"ok": 1}


class MemoryClient:
    def __init__(self):
        self.admin = MemoryAdmin()
        self.databases = {}

    def __getitem__(self, name):
        if name not in self.databases:
            self.databases[name] = MemoryDatabase()
        return self.databases[name]


class DownAdmin:
    def command(self, name, *args, **kwargs):
        raise ConnectionError("timed out contacting mongodb+srv://user:secret@cluster.example")


class DownClient:
    def __init__(self):
        self.admin = DownAdmin()

    def __getitem__(self, name):
        raise ConnectionError("timed out contacting mongodb+srv://user:secret@cluster.example")
