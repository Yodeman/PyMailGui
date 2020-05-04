from tkinter import *
from p_python.GUI.Tools.windows import PopupWindow

class HelpPopup(PopupWindow):

    myfont = 'system'
    mywidth = 78

    def __init__(self, appname, helptext, iconfile=None, showsource=lambda:0):
        super().__init__(appname, 'Help', iconfile)
        from tkinter.scrolledtext import ScrolledText
        bar = Frame(self)
        bar.pack(side=BOTTOM, fill=X)
        code = Button(bar, bg='beige', text='Source')
        quit = Button(bar, bg='beige', text='Cancel', command=self.destroy)
        code.pack(pady=1, side=LEFT)
        quit.pack(pady=1, side=LEFT)
        text = ScrolledText(self)
        text.config(font=self.myfont)
        text.config(width=self.mywidth)
        text.config(bg='steelblue', fg='white')
        text.insert('0.0', helptext)
        text.pack(expand=YES, fill=BOTH)
        self.bind('<Return>', (lambda event: self.destory))

def askPasswordWindow(appname, prompt):
    """
    a modal dialog to input password string
    """
    win = PopupWindow(appname, 'Prompt')
    Label(win, text=prompt).pack(side=LEFT)
    entVar = StringVar()
    ent = Entry(win, textvariable=entVar, show='*')
    ent.pack(side=RIGHT, expand=YES, fill=X)
    ent.bind('<Return>', lambda event: win.destroy())
    ent.focus_set()
    win.grab_set()
    win.wait_window()
    win.update()
    return entVar.get()

class BusyBoxWait(PopupWindow):
    def __init__(self, appname, message):
        super().__init__(appname, message)
        self.protocol('WM_DELETE_WINDOW', lambda:0)
        label = Label(self, text=message + '...')
        label.config(height=10, width=40, cursor='watch')
        label.pack()
        self.makeModal()
        self.message, self.label = message, label

    def makeModal(self):
        self.focus_set()
        self.grab_set()

    def changeText(self, newtext):
        self.label.config(text=self.message + ': ' + newtext)

    def quit(self):
        self.destory()

class BusyBoxNowait(BusyBoxWait):
    def makeModal(self):
        pass
