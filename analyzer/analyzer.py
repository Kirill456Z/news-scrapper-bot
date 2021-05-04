import spacy
import re
from collections import Counter


class TextAnalyzer:
    def __init__(self, text):
        text = re.sub('\n', ' ', text)
        text = re.sub(' +', ' ', text)
        text_list = text.split('.')
        self.nouns = Counter()
        self.other = Counter()
        nlp = spacy.load("ru_core_news_sm")
        for doc in nlp.pipe(text_list, disable=["ner"]):
            for token in doc:
                if not token.is_punct and not token.is_stop and not token.is_digit and not token.is_space:
                    if token.pos_ == "NOUN" or token.pos_ == "PROPN":
                        self.nouns[token.lemma_] += 1
                    self.other[token.lemma_] += 1

    def get_description(self, count):
        return self.nouns.most_common(count)

    def get_stats(self):
        lengths = [0 for i in range(30)]
        for word in self.other.most_common():
            lengths[len(word[0])] += word[1]
        while lengths[-1] == 0:
            del lengths[-1]
        return lengths

    def __iadd__(self, other):
        self.other += other.other
        return self
