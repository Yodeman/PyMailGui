helpfile = 'PyMailGuiHelp.html'

def showHtmlHelp(help=helpfile):
    import os, webbrowser
    mydir = os.path.dirname(__file__)
    mydir = os.path.abspath(mydir)
    webbrowser.open_new('file://' + os.path.join(mydir, helpfile))

helptext = """PyMailGui
written by Paul,
May, 2020 with the help of,
Programming Python, 4th Edition
Mark Lutz.

A multiwindow interface for processing email, both online and offline.
Just navigate through the app and enjoy it.
"""
