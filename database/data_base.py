import sqlite3
from news_agregation.document_scraper import Document
from news_agregation.theme_scraper import Theme
from time import strftime
import re
import datetime


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


class Database:
    def __init__(self):
        self.connection = sqlite3.connect("news.db")
        self.cur = self.connection.cursor()
        self.cur.execute('''
        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url VARCHAR(255),
            title VARCHAR(255),
            text VARCHAR(2047),
            date TIMESTAMP
        )''')
        self.cur.execute('''
        CREATE TABLE IF NOT EXISTS allArticles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url VARCHAR(255),
            title VARCHAR(255),
            date TIMESTAMP,
            theme_id INTEGER
        )''')

    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def get_newest_themes(self, count):
        themes = []
        cursor = self.cur.execute("SELECT * FROM themes ORDER BY date DESC LIMIT " + str(count))
        for row in cursor.fetchall():
            time_struct = datetime.datetime.strptime(row[4], "%Y-%m-%dT%H:%M")
            theme = Theme(url=row[1], title=row[2], text=row[3], timestamp=time_struct)
            themes.append(theme)
        return themes

    def get_theme(self, title):
        row = self.cur.execute("SELECT * FROM themes WHERE title = '" + title + "'").fetchone()
        if row is None:
            return None
        table_name = "Theme" + str(row[0])
        urls = []
        for url in self.cur.execute("SELECT url FROM " + table_name).fetchall():
            urls.append(url[0])
            pass
        theme = Theme(url=row[1], title=row[2], text=row[3], documents=urls, theme_id=row[0])
        return theme

    def get_newest_documents(self, count, theme_id=None):
        cur = self.connection.cursor()
        documents = []
        if theme_id is None:
            cursor = cur.execute("SELECT * FROM allArticles ORDER BY date DESC LIMIT " + str(count))
            for row in cursor.fetchall():
                theme_id = row[4]
                row = cur.execute(
                    "SELECT * FROM Theme" + str(theme_id) + " WHERE url = '" + row[1] + "'").fetchone()
                time_struct = datetime.datetime.strptime(row[3], "%Y-%m-%dT%H:%M")
                doc = Document(url=row[1], title=row[2], datetime=time_struct, text=row[4], tags=row[5].split(';'))
                documents.append(doc)
        else:
            cursor = cur.execute("SELECT * FROM Theme" + str(theme_id) + " ORDER BY date DESC LIMIT " + str(count))
            for row in cursor.fetchall():
                time_struct = datetime.datetime.strptime(row[3], "%Y-%m-%dT%H:%M")
                doc = Document(url=row[1], title=row[2], datetime=time_struct, text=row[4], tags=row[5])
                documents.append(doc)

        return documents

    def get_all_documents(self, theme_id):
        cur = self.connection.cursor()
        cursor = cur.execute("SELECT * FROM Theme" + str(theme_id) + " ORDER BY date DESC")
        last_row = cursor.fetchone()
        while last_row is not None:
            yield Document(last_row[1], last_row[2], last_row[3], last_row[4], last_row[5].split(';'))
            last_row = cursor.fetchone()

    def get_document(self, title):
        row = self.cur.execute("SELECT theme_id FROM allArticles WHERE title = '" + title + "'").fetchone()
        if row is None:
            return None
        table_name = "Theme" + str(row[0])
        row = self.cur.execute("SELECT * FROM " + table_name + " WHERE title = '" + title + "'").fetchone()
        doc = Document(row[1], row[2], row[3], row[4], row[5].split(';'))
        return doc

    def is_present(self, url):
        return not self.cur.execute("SELECT 1 FROM themes WHERE url = '" + url + "'").fetchone() is None

    def insert(self, theme: Theme):
        if len(theme.documents) == 0:
            return
        cursor = self.cur.execute("SELECT * FROM themes WHERE url = '" + theme.url + "'")
        theme_record = cursor.fetchone()
        if theme_record is None:
            theme_str = "('" + theme.url + "','" + theme.title + "','" + theme.text + "')"
            self.cur.execute("INSERT INTO themes (url, title, text) VALUES" + theme_str)
            table_id = self.cur.lastrowid
            table_name = "Theme" + str(table_id)
            self.cur.execute("CREATE TABLE " + table_name +
                             '''(id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 url VARCHAR(255),
                                 title VARCHAR(255),
                                 date TIMESTAMP,
                                 text VARCHAR(65535),
                                 tags VARCHAR(255)
                             )''')
        else:
            table_id = theme_record[0]
            table_name = "Theme" + str(table_id)
        for index, document_url in enumerate(theme.documents):
            self._insert_document(document_url, table_id)
        last_update = self.cur.execute("SELECT MAX(date) FROM " + table_name).fetchone()[0]
        self.cur.execute("UPDATE themes SET date = '" + last_update + "' WHERE url = '" + theme.url + "'")
        self.connection.commit()

    def _insert_document(self, doc_url, theme_id):
        table_name = "Theme" + str(theme_id)
        doc_record = self.cur.execute("SELECT 1 FROM " + table_name + " WHERE url = '" + doc_url + "'")
        if doc_record.fetchone() is None:
            document = Document(doc_url)
            text = document.text.replace("'", "''")
            text = re.sub(r'\n\s*\n', '\n\n', text)
            time_str = strftime("%Y-%m-%dT%H:%M", document.time)
            doc_str = "('" + document.url + "','" + document.title.replace("'", "''") + "','" + time_str
            doc_str += "','" + text + "','" + ';'.join(document.tags).replace("'", "''") + "')"
            self.cur.execute("INSERT INTO " + table_name + " (url,title,date,text,tags) VALUES " + doc_str)
            art_str = "('" + document.url + "','" + document.title.replace("'","''") + "','" + time_str + "'," + str(theme_id) + ")"
            self.cur.execute("INSERT INTO allArticles (url,title,date,theme_id) VALUES " + art_str)
            self.connection.commit()
            return True
        else:
            return False
