import urllib.request
from html.parser import HTMLParser

class SiteSpecificParser(HTMLParser):
    def __init__(self, *, convert_charrefs = True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.is_wordlist = False
        self.wordlist = ""

    def handle_starttag(self, tag, attrs):
        if tag == "span":
            for name, value in attrs:
                if name == "class" and value == "mt":
                    self.is_wordlist = True
                    break
    
    def handle_endtag(self, tag):
        if tag == "span":
            self.is_wordlist = False
    
    def handle_data(self, data):
        if self.is_wordlist:
            self.wordlist = data
    
filename = "datasets/dico.txt"
baseurl="https://www.listesdemots.net/touslesmots" 

# This is to get how many pages and how many words if I need to generalise it
# <a class=pg href=touslesmotspage1548.htm>1548</a>
# <h2>Il y a 416349 mots</h2>

TOTAL_PAGE_NUMBER = 1548

with open(filename , "w" ) as file:
    wordcount = 0
    for page_num in range(1, TOTAL_PAGE_NUMBER + 1):
        if page_num == 1:
            url = baseurl + ".htm"
        else:
            url = baseurl + str(page_num) +".htm"

        print(f"starting page {page_num} at", url)

        with urllib.request.urlopen(url) as page:
            content = page.read()
            content = content.decode("utf8")
        
        parser = SiteSpecificParser()
        parser.feed(content)
        wordlist = parser.wordlist.strip().split()
        
        for word in wordlist:
            file.write(word + "\n")
            print("|", end="")
        wordcount += len(wordlist)

        print(f"\npage {page_num} : OK ({wordcount}/{416349})")
