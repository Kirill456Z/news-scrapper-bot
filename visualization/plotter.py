import matplotlib.pyplot as plt


class Ploter:
    def __init__(self, analyzed):
        lengths = analyzed.get_stats()
        plt.plot(range(len(lengths)), lengths)
        plt.suptitle("Распределение длин слов", fontsize=20)
        plt.xlabel("Длина слова")
        plt.ylabel("Колличество слов")
        plt.savefig('lengths.png', fmt='png')
        plt.cla()
        words = [analyzed.other.most_common()[i][0] for i in range(15)]
        freq = [analyzed.other.most_common()[i][1] for i in range(15)]
        plt.suptitle("Часто встречающиеся слова")
        plt.ylabel("Колличество вхождений")
        plt.xlabel("Слово")
        plt.bar(words, freq)
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.savefig('frequencies.png', fmt='png')
        plt.cla()
