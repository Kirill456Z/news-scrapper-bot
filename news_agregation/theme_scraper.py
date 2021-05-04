from news_agregation.document_scraper import Document
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
import re


class Theme:
    def __init__(self, url=None, title=None, text=None, documents=None, theme_id=None, timestamp=None):
        self.url = ""
        if title is None:
            self.url = url
            try:
                response = requests.get(url)
            except Exception as e:
                raise ConnectionError("Invalid url")
            if response.status_code != 200:
                raise ConnectionError("Resource unavailable")
            html = response.content.decode(response.apparent_encoding)
            self.soup = BeautifulSoup(html, 'lxml')
        self.title = title
        self.text = text
        self.documents = documents if documents is not None else []
        self.id = theme_id
        self.time = timestamp


class Story(Theme):
    def __init__(self, url):
        super().__init__(url)
        one_story = self.soup.body.main.div.div.div
        self.title = one_story.div.h1.text
        self.text = one_story.find("div", {"class": "text"}).text
        story_list = self.soup.find("div", {"class": "storyList"})
        for document in story_list.contents:
            if not isinstance(document, Tag):
                document = BeautifulSoup(document, 'lxml')
            try:
                doc_relative_url = document.div.h2.a['href']
                doc_url = urljoin("https://www.interfax.ru", doc_relative_url)
                self.documents.append(doc_url)
            except (AttributeError, TypeError):
                pass


class Chronicle(Theme):
    def __init__(self, url):
        super().__init__(url)
        container = self.soup.body.main.div.section
        self.title = container.h1.text
        self.text = container.div.text
        story_list = self.soup.find("div", {"class": "chronicles__wrap"})
        self.documents = []
        for timeline in story_list.contents:
            if not isinstance(timeline, Tag):
                timeline = BeautifulSoup(timeline, 'lxml')
            for document in timeline.contents:
                if not isinstance(document, Tag):
                    document = BeautifulSoup(document, 'lxml')
                try:
                    doc_relative_url = document.a['href']
                    doc_url = urljoin("https://www.interfax.ru", doc_relative_url)
                    self.documents.append(doc_url)
                except (AttributeError, TypeError):
                    pass
