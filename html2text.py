from html.parser import HTMLParser

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = '[Extracted HTML text]'
        self.save = 0
        self.last = ''

    def addtext(self, new):
        if self.save > 0:
            self.text += new
            self.last = new

    def addeoln(self, force=False):
        if force or self.last != '\n':
            self.addtext('\n')

    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'div', 'table', 'h1', 'h2', 'li'):
            self.save += 1
            self.addeoln()
        elif tag == 'td':
            self.addeoln()
        elif tag == 'style':
            self.save -= 1
        elif tag == 'br':
            self.addeoln(True)
        elif tag == 'a':
            alts = [pair for pair in attrs if pair[0] == 'alt']
            if alts:
                name, value = alts[0]
                self.addtext('[' + value.replace('\n', '') + ']')

    def handle_endtag(self, tag):
        if tag in ('p', 'div', 'table', 'h1', 'h2', 'li'):
            self.save -= 1
            self.addeoln()
        elif tag == 'style':
            self.save += 1

    def handle_data(self, data):
        data = data.replace('\n', '')
        data = data.replace('\t', ' ')
        if data != ' ' * len(data):
            self.addtext(data)

    def handle_entityref(self, name):
        xlate = dict(lt='<', gt='>', amp='&', nbsp='').get(name, '?')
        if xlate:
            self.addtext(xlate)

def html2text(text):
    try:
        hp = Parser()
        hp.feed(text)
        return (hptext)
    except:
        return text

if __name__ == "__main__":
    import sys, tkinter
    text = open(sys.argv[1], 'r').read()
    text = html2text(text)
    t = tkinter.Text()
    t.insert('1.0', text)
    t.pack()
    t.mainloop()