import html
import json
import logging
import traceback

from telegram import ParseMode
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

from news_agregation.site_scraper import Site
from database.data_base import Database
from analyzer.analyzer import TextAnalyzer
import matplotlib.pyplot as plt
from visualization.plotter import Ploter
from collections import Counter
import os

PORT = os.environ.get('PORT', '8443')


class Bot:

    def __init__(self):
        self.site = Site()
        self.BOT_TOKEN = os.environ.get("TOKEN")
        self.DEVELOPER_CHAT_ID = os.environ.get("CHAT_ID")

        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        self.logger = logging.getLogger(__name__)
        self.updater = Updater(self.BOT_TOKEN)
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("help", self.help_command))
        dp.add_handler(CommandHandler("new_docs", self.new_docs))
        dp.add_handler(CommandHandler("new_topics", self.new_topics))
        dp.add_handler(CommandHandler("topic", self.show_topic))
        dp.add_handler(CommandHandler("doc", self.show_doc))
        dp.add_handler(CommandHandler("words", self.analyzer))
        dp.add_handler(CommandHandler("describe_doc", self.describe_doc))
        dp.add_handler(CommandHandler("describe_topic", self.describe_topic))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.process_input))
        dp.add_error_handler(self.error_handler)

    def start(self, update: Update, _: CallbackContext):
        """Send a message when the command /start is issued."""
        user = update.effective_user
        update.message.reply_markdown_v2(
            f'Привет, {user.mention_markdown_v2()}\!'
        )
        self.help_command(self, update, _)

    def update(self):
        self.site.update()

    def help_command(self, update: Update, _: CallbackContext):
        """Send a message when the command /help is issued."""
        message = "Доступные команды: \n /new_docs [N] - показать N последних статей \n" \
                  "/new_topics [N] - показать последнии N тем, в которых были обновления\n" \
                  "/topic [Title] - информация о теме с заголовком Title \n" \
                  "/doc [Title] - содержимое статьи с заголовком Title\n" \
                  "/words [Title] - ключевые слова темы с заголовком Title \n" \
                  "/describe_doc [Title] - статистика по словам статьи Title \n" \
                  "/describe_topic [Title] - статистика по теме с заголовком Title"

        update.message.reply_text(message)

    def new_docs(self, update, context):
        error_str = "Некорректный ввод, после команды должно быть одно число - колличество документов, которые вы " \
                    "хотите увидеть. (Например, команда <b>/new_docs 10</b> покажет 10 документов) "
        db = Database()
        if len(context.args) == 0:
            docs_count = 5
        elif len(context.args) > 1:
            self.echo(update, error_str)
            docs_count = None
        else:
            try:
                docs_count = int(context.args[0])
            except (TypeError, ValueError):
                self.echo(update, error_str)
                docs_count = None
        if docs_count is not None:
            documents = db.get_newest_documents(docs_count)
            result = "\n".join(
                ["{}: {}".format(documents[i].time.strftime("%m/%d/%Y, %H:%M"), documents[i].title) for i in
                 range(len(documents))])
            self.echo(update, result)

    def new_topics(self, update, context):
        error_str = "Некорректый ввод, после команды должно быть одно число - колличество тем, информацию по которым вы хотите увидеть (Например /new_topics 10 покажет первые 10 тем)"
        if len(context.args) == 0:
            topics_count = 5
        elif len(context.args) > 1:
            self.echo(update, error_str)
            topics_count = None
        else:
            try:
                topics_count = int(context.args[0])
            except:
                self.echo(update, error_str)
                topics_count = None
        if topics_count is not None:
            db = Database()
            themes = db.get_newest_themes(topics_count)
            result = "\n".join(
                ["{}: {}".format(themes[i].time.strftime("%m/%d/%Y, %H:%M"), themes[i].title) for i in
                 range(len(themes))])
            self.echo(update, result)

    def show_topic(self, update, context):
        db = Database()
        topic_title = " ".join(context.args)
        theme = db.get_theme(topic_title)
        if theme is None:
            self.echo(update, "Мне не удалось найти тему с таким названием. \U0001F614")
        else:
            docs = db.get_newest_documents(5, theme_id=theme.id)
            res = "<b>{}</b>".format(theme.title)
            res += "\n Последние новости в этой теме:\n"
            for index, doc in enumerate(docs):
                res += "{}. {}\n".format(str(index + 1), doc.title)
            self.echo(update, res)

    def show_doc(self, update, context):
        db = Database()
        doc_title = " ".join(context.args)
        doc = db.get_document(doc_title)
        if doc is None:
            self.echo(update, "Мне не удалось найти новость с таким заголовком. \U0001F614")
        else:
            res = "<b>{}</b>\n{}\n{}".format(doc.title, doc.text, doc.tags)
            self.echo(update, res)

    def analyzer(self, update, context):
        db = Database()
        theme_title = " ".join(context.args)
        theme = db.get_theme(theme_title)
        if theme is None:
            self.echo(update, "Mне не удалось найти тему с таким заголовком. \U0001F614")
        else:
            last_docs = db.get_newest_documents(10, theme.id)
            nouns = TextAnalyzer(theme.text).nouns
            for doc in last_docs:
                for item, count in TextAnalyzer(doc.text).nouns.most_common(20):
                    nouns[item] += count
            res = "Слова характеризующие тему: \n"
            for word in nouns.most_common(10):
                res += word[0].capitalize() + "\n"
            self.echo(update, res)

    def describe_doc(self, update, context):
        db = Database()
        doc_title = " ".join(context.args)
        doc = db.get_document(doc_title)
        if doc is None:
            self.echo(update, "Мне не удалось найти новость с таким заголовком. \U0001F614")
        else:
            analyzer = TextAnalyzer(doc.title + doc.text)
            Ploter(analyzer)
            update.message.reply_photo(photo=open("frequencies.png", 'rb'))
            update.message.reply_photo(photo=open("lengths.png", 'rb'))

    def describe_topic(self, update, context):
        db = Database()
        theme_title = " ".join(context.args)
        theme = db.get_theme(theme_title)
        if theme is None:
            self.echo(update, "Mне не удалось найти тему с таким заголовком. \U0001F614")
            return
        res = "В теме <b>{}</b> содержится {} новостей\n".format(theme.title, str(len(theme.documents)))
        total_length = 0
        analyzer = TextAnalyzer("")
        for doc in db.get_all_documents(theme.id):
            total_length += len(doc.text)
            analyzer += TextAnalyzer(doc.title + doc.title)
        res += "Средняя длина новости: {} символов".format(str(total_length / len(theme.documents)))
        self.echo(update, res)
        Ploter(analyzer)
        update.message.reply_photo(photo=open("frequencies.png", 'rb'))
        update.message.reply_photo(photo=open("lengths.png", 'rb'))

    def process_input(self, update: Update, _: CallbackContext):
        self.echo(update, "Неизвестная команда, напечатайте <b>/help</b> чтобы увидеть список доступных команд.")

    def echo(self, update, text):
        update.message.reply_html(text);

    def error_handler(self, update: Update, context: CallbackContext):
        """Log the error and send a telegram message to notify the developer."""
        self.logger.error(msg="Exception while handling an update:", exc_info=context.error)
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = ''.join(tb_list)
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            f'An exception was raised while handling an update\n'
            f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
            '</pre>\n\n'
            f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
            f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
            f'<pre>{html.escape(tb_string)}</pre>'
        )

        context.bot.send_message(chat_id=self.DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML)

    def launch_bot(self):
        print("Current PORT : {}".format(PORT))
        self.updater.start_webhook(listen='0.0.0.0', port=int(PORT), url_path=self.BOT_TOKEN,
                                   webhook_url="https://news-scrapper-bot.herokuapp.com/" + self.BOT_TOKEN)
        self.updater.idle()
