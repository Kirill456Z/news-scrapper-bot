import requests
from bs4 import BeautifulSoup, Tag
import re
from urllib.parse import urljoin
from news_agregation.theme_scraper import Theme, Story, Chronicle
from database.data_base import Database
from itertools import count


class Site:
    def __init__(self):
        self.db = Database()
        self.themes = []
        url = "https://www.interfax.ru/story/"
        try:
            response = requests.get(url)
        except Exception as e:
            raise ConnectionError("Invalid url")
        if response.status_code != 200:
            raise ConnectionError("Resource unavailable")
        html = response.content.decode(response.apparent_encoding)
        soup = BeautifulSoup(html, 'lxml')
        pages_count = int(soup.find("div", {"class": "allPNav"}).find_all("a")[-1].get_text())
        self._parse_single_page(url)
        print("Scraping themes...")
        for i in range(2, pages_count + 1):
            print("\r(parsed {} pages of {})".format(str(i), str(pages_count)), end = "")
            try:
                page_url = url + "page_" + str(i)
                self._parse_single_page(page_url)
            except ConnectionError:
                print("could not parse {} due to connection error".format(url))
                pass
        print("\nThemes scraped")

    def _parse_single_page(self, url):
        try:
            response = requests.get(url)
        except Exception as e:
            raise ConnectionError("Invalid url")
        if response.status_code != 200:
            raise ConnectionError("Resource unavailable")
        html = response.content.decode(response.apparent_encoding)
        soup = BeautifulSoup(html, 'lxml')
        for stories in soup.find_all("div", {"class": "allStory"}):
            if not isinstance(stories, Tag):
                stories = BeautifulSoup(stories, 'lxml')
            for story in stories.contents:
                if not isinstance(story, Tag):
                    story = BeautifulSoup(story, 'lxml')
                try:
                    url = story.a['href']
                    doc_url = urljoin("https://www.interfax.ru", url)
                    self.themes.append(doc_url)
                except (AttributeError, TypeError) as e:
                    # print("error ", str(e))
                    pass

    def update(self):
        print("Updating database")
        for index, theme_url in enumerate(self.themes):
            try:
                if re.match(r"https://www.interfax.ru/story/[0-9]{3}", theme_url):
                    theme = Story(theme_url)
                else:
                    theme = Chronicle(theme_url)
                self.db.insert(theme)
                print("Updated {} themes of {}, last one: {: <150} ".format(str(index + 1),str(len(self.themes)),theme.url + " ( " + theme.title + " ) "))
            except (AttributeError, ConnectionError) as e:
                print("Error, could not parse {} : ".format(theme_url) + str(e))
