from conf.config import Config


class DBMSManager:
    def __init__(self):
        self._loaded_dbms = dict()

    def __getitem__(self, item: str):
        if item not in self._loaded_dbms:
            dbms = None
            if item == "mongodb":
                from pymongo import MongoClient

                uri = Config()["MONGODB_URI"]
                dbms = MongoClient(uri)

            elif item == "mongodb_mm1":
                from pymongo import MongoClient

                uri = Config()["MONGODB_MM1_URI"]
                dbms = MongoClient(uri)
            elif item == "elasticsearch":
                from elasticsearch import Elasticsearch

                dbms = Elasticsearch(Config()["ES_URL"])

            if dbms:
                self._loaded_dbms[item] = dbms

        return self._loaded_dbms.get(item)
