# pop3 email server machine, user
popservername = 'pop.gmail.com'
popusername1 = 'oyelabipaul@gmail.com'
popusername2 = 'poyelabi29@gmail.com'

# smtp
smtpservername = 'smtp.gmail.com'

myaddress = 'oyelabipaul@gmail.com'
mysignature = 'Thanks\n--Pauli--'

smtpuser = 'oyelabipaul@gmail.com'
smtppassword = ''

import os, wraplines
mysourcedir = os.path.dirname(os.path.abspath(wraplines.__file__))
sentmailfile = mysourcedir + 'sentmail.txt'

listheaders = ('Subject', 'From', 'Date', 'To', 'X-Mailer')
viewheaders = ('Bcc',)

listbg = 'indianred'
listfg = 'black'
listfont = ('courier', 9, 'bold')

viewbg = 'light blue'
viewfg = 'black'
viewfont = ('courier', 10, 'bold')
viewheight = 18

partfg = None
partbg = None

wrapsz = 90

okayToOpenParts = True
verifyPartOpens = True
verifyHTMLTextOpen = False

maxPartButtons = 8

fetchEncoding = 'latin-1'

mainTextEncoding = 'ascii'
attachmentTextEncoding = 'ascii'

headersEncodeTo = None

showHelpAsText = True
showHelpAsHTML = True

skipTextOnHtmlPart = False

fetchlimit = 50

listWidth = None
listHeight = None

repliesCopyToAll = True