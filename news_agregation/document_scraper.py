import re
import requests
from bs4 import BeautifulSoup
import time


class Document:
    def __init__(self, url=None, title=None, datetime=None, text=None, tags=None):
        if title is None:
            self.url = url
            if not re.match(r"https://www.interfax.ru/[a-z]*/[0-9]{6}", url):
                raise AttributeError("invalid url, must be interfax news page!")
            try:
                response = requests.get(url)
            except Exception as e:
                raise ConnectionError("Invalid url")
            if response.status_code != 200:
                raise ConnectionError("Resource unavailable")
            html = response.content.decode(response.apparent_encoding)
            soup = BeautifulSoup(html, 'lxml')
            timestr = soup.find('time')['datetime']
            self.time = time.strptime(timestr, "%Y-%m-%dT%H:%M")
            article = soup.find("article", {"itemprop": "articleBody"})
            self.title = article.find("h1", {"itemprop": "headline"}).extract().text
            self.text = article.text
            tags = soup.find("div", {"class": "textMTags"})
            self.tags = []
            for tag in tags.find_all("a"):
                self.tags.append(tag.text)
        else:
            self.url = url
            self.title = title
            self.text = text
            self.time = datetime
            self.tags = tags if tags is not None else []

    def __str__(self):
        res = "Document object: \n"
        res += "URL: " + self.url + "\n"
        res += "Title: " + self.title + "\n"
        res += "Tags: " + str(self.tags) + "\n"
        return res
