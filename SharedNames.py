"""
objects shared by all window classes and mail file
"""

# used in all windows, icon titles
appname = 'PyMailGui 3.0'

# used for list save, open, delete; also for sent-mail file
saveMailSeparator = 'PyMailGui' + ('-'*60) + 'PyMailGui\n'

# currently viewed mail save files; also for sent mail filr
openSaveFiles = {}

# standard library services
import sys, os, email.utils, email.message, webbrowser, mimetypes
from tkinter import *
from tkinter.simpledialog import askstring
from tkinter.filedialog import SaveAs, Open, Directory
from tkinter.messagebox import showinfo, showerror, askyesno

from p_python.GUI.Tools import windows
from p_python.GUI.Tools import threadtools
from p_python.internet.Email import mailtools
from p_python.TextEditor import PyNote

import mailconfig       # user config
import popuputil        # help, busy, passwd pop-up windows
import wraplines        # wrap long message lines
import messagecache     # remember already loaded mail
import html2text        
import PyMailGuiHelp

def printStack(exc_info):
    print(exc_info[0])
    print(exc_info[1])
    import traceback
    try:
        traceback.print_tb(exc_info[2], file=sys.stdout)
    except:
        log = open('_pymailerrlog.txt', 'a')
        log.write('-'*80)
        traceback.print_tb(exc_info[2], file=log)

# thread busy counters for threads run by this GUI
# sendingBusy shared by all send windows, used by main window quit

loadingHdrsBusy = threadtools.ThreadCounter()
deletingBusy = threadtools.ThreadCounter()
loadingMsgBusy = threadtools.ThreadCounter()
sendingBusy = threadtools.ThreadCounter()
