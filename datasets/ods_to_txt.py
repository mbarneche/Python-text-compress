import time
import urllib.request
from html.parser import HTMLParser

class WordListParser(HTMLParser):
    def __init__(self, convert_charrefs = True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.inside_span = False
        self.is_wordlist = False
        self.wordlist = ""

    def handle_starttag(self, tag, attrs):
        if tag == "span":
            for name, value in attrs:
                if name == "class" and value == "mt":
                    self.is_wordlist = True
                elif name == "class" and (value == "rd" or value == "gn"):
                    self.inside_span = True
    
    def handle_endtag(self, tag):
        if tag == "span":
            if self.inside_span:
                self.inside_span = False
            else:
                self.is_wordlist = False
    
    def handle_data(self, data):
        if self.is_wordlist:
            self.wordlist += data

LNG = { "fr": ("https://www.listesdemots.net/touslesmots", 416349, "page", 1548),
        "en": ("https://www.bestwordlist.com/allwords", 281494, "page", 950),
        "es": ("https://www.listasdepalabras.es/todaspalabras", 635040, "pagina", 2343),
        "it": ("https://www.listediparole.it/tutteleparole", 664005, "pagina", 2535),
        "de": ("https://www.wortlisten.com/alleworter", 170635, "seite", 526),
        "ro": ("https://www.listedecuvinte.com/toatecuvintele", 610767, "pagina", 2240)}

def extract_html(url):
    with urllib.request.urlopen(url) as page:
        content = page.read()
        content = content.decode("utf8")
    return content

def ods_to_txt(filename, language, verbose=False):
    with open(filename , "w" ) as file:
        wordcount = 0
        baseurl = LNG[language][0]
        for page_num in range(1, LNG[language][3] + 1):
            if page_num == 1:
                url = baseurl + ".htm"
            else:
                url = baseurl + LNG[language][2] + str(page_num) + ".htm"

            if verbose:
                print(f"starting page {page_num} at", url)
            
            content = extract_html(url)
            parser = WordListParser()
            parser.feed(content)
            wordlist = parser.wordlist.strip().split()
            
            for word in wordlist:
                file.write(word + "\n")
                if verbose:
                    print("|", end="")
   
            if verbose:
                wordcount += len(wordlist)
                print(f"\npage {page_num} : OK ({wordcount}/{LNG[language][1]})")

if __name__ == "__main__":
    for language in LNG.keys():
        filename = f"datasets/dico_{language}.txt"
        print("\nstarting", language)
        st = time.time()
        ods_to_txt(filename, language)
        et = time.time()
        print(f"finished {language} in {et - st:.03f} seconds")
