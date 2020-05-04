from SharedNames import *
from ViewWindows import ViewWindow, WriteWindow, ReplyWindow, ForwardWindow

# general structure for both file and server message lists

class PyMailCommon(mailtools.MailParser):
    # lass attrs shared by all list windows
    threadLoopStarted = False
    queueChecksPerSecond = 20
    queueDelay = 1000//queueChecksPerSecond
    queueBatch = 5

    # all windows use same dialogs: remember last dirs
    openDialog = Open(title=appname + ': Open Mail File')
    saveDialog = SaveAs(title=appname + ': Append Mail File')

    # avoid downloading same message in parallel
    beingFetched = set()

    def __init__(self):
        self.makeWidgets()
        if not PyMailCommon.threadLoopStarted:
            PyMailCommon.threadLoopStarted = True
            threadtools.threadChecker(self, self.queueDelay, self.queueBatch)

    def makeWidgets(self):
        # add all/none checkbtn at bottom
        tools = Frame(self, relief=SUNKEN, bd=2, cursor='hand2')
        tools.pack(side=BOTTOM, fill=X)
        self.allModeVar = IntVar()
        chk = Checkbutton(tools, text='All')
        chk.config(variable = self.allModeVar, command=self.onCheckAll)
        chk.pack(side=RIGHT)

        # add main buttons at bottom toolbar
        for (title, callback) in self.actions():
            if not callback:
                sep = Label(tools, text=title)
                sep.pack(side=LEFT, expand=YES, fill=BOTH)
            else:
                Button(tools, text=title, command=callback).pack(side=LEFT, padx=5, pady=5)

        # add multiselect listbox with scrollbars
        listwide = mailconfig.listWidth or 74
        listhigh = mailconfig.listHeight or 15
        mails = Frame(self)
        vscroll = Scrollbar(mails)
        hscroll = Scrollbar(mails, orient='horizontal')
        fontsz = (sys.platform[:3]=='win' and 8) or 10
        listbg = mailconfig.listbg or 'white'
        listfg = mailconfig.listfg or 'black'
        listfont = mailconfig.listfont or ('courier', fontsz, 'normal')
        listbox = Listbox(mails, bg=listbg, fg=listfg, font=listfont)
        listbox.config(selectmode=EXTENDED)
        listbox.config(width=listwide, height=listhigh)
        listbox.bind('<Button-1>', (lambda event: self.onViewRawMail()))

        # crosslink listbox and scrollbars
        vscroll.config(command=listbox.yview, relief=SUNKEN)
        hscroll.config(command=listbox.xview, relief=SUNKEN)
        listbox.config(yscrollcommand=vscroll.set, relief=SUNKEN)
        listbox.config(xscrollcommand=hscroll.set)

        # pack last = clip first
        mails.pack(side=TOP, expand=YES, fill=BOTH)
        vscroll.pack(side=RIGHT, fill=BOTH)
        hscroll.pack(side=BOTTOM, fill=BOTH)
        listbox.pack(side=LEFT, expand=YES, fill=BOTH)
        self.listbox = listbox

    # event handlers
    def onCheckAll(self):
        # all or none click
        if self.allModeVar.get():
            self.listbox.select_set(0, END)
        else:
            self.listbox.select_clear(0, END)

    def onViewRawMail(self):
        # possibly threaded: view selected messages - raw text headers, body
        msgnums = self.verifySelectedMsgs()
        if msgnums:
            self.getMessages(msgnums, after=lambda:self.contVieRaw(msgnums))
            
    def contVieRaw(self, msgnums, pyedit=True):
        for msgnum in msgnums:
            fulltext = self.getMessage(msgnum)
            if not pyedit:
                # display in scrolledtext
                from tkinter.scrolledtext import ScrolledText
                window = windows.QuietPopupWindow(appname, 'raw message viewer')
                browser = ScrolledText(window)
                browser.insert('0.0', fulltext)
                browser.pack(expand=YES, fill=BOTH)

            else:
                # display in PyNote
                #wintitle = ' - raw message text'
                browser = PyNote.TextEditorMainPopup(self)
                browser.update()
                browser.setAllText(fulltext)
                browser.clearModified()

    def onViewFormatMail(self):
        msgnums = self.verifySelectedMsgs()
        if msgnums:
            self.getMessages(msgnums, after=lambda: self.contViewFmt(msgnums))

    def contViewFmt(self, msgnums):
        for msgnum in msgnums:
            fulltext = self.getMessage(msgnum)
            message = self.parseMessage(fulltext)
            type, content = self.findMainText(message)
            if type in ['text/html', 'text/xml']:
                content = html2text.html2text(content)
            content = wraplines.wrapText1(content, mailconfig.wrapsz)
            ViewWindow(headermap = message,
                        showtext = content,
                        origmessage = message)
            # non-multipart content-type text/HTML
            if type == 'text/html':
                if ((not mailconfig.verifyHTMLTextOpen) or 
                    askyesno(appname, 'Open message text in browser?')):

                    type, asbytes = self.findMainText(message, asStr=False)
                    try:
                        from tempfile import gettempdir
                        tempname = os.path.join(gettempdir(), 'pymailgui.html')
                        tmp = open(tempname, 'wb')
                        tmp.write(asbytes)
                        webbrowser.open_new('file://' + tempname)

                    except:
                        showerror(appname, 'Cannot open in browser')

    def onWriteMail(self):
        starttext = '\n'
        if mailconfig.mysignature:
            starttext += '\n%s' % mailconfig.mysignature
        From = mailconfig.myaddress
        WriteWindow(starttext = starttext,
                    headermap = dict(From=From, Bcc=From))

    def onReplyMail(self):
        msgnums = self.verifySelectedMsgs()
        if msgnums:
            self.getMessages(msgnums, after=lambda: self.contReply(msgnums))

    def contReply(self, msgnums):
        for msgnum in msgnums:
            fulltext = self.getMessage(msgnum)
            message = self.parserMessage(fulltext)
            maintext = self.formatQuoteMainText(message)

            From = mailconfig.myaddress
            To = message.get('From', '')
            Cc = self.replyCopyTo(message)
            Subj = message.get('Subject', '(no subject)')
            Subj = self.decodeHeader(Subj)
            if Subj[:4].lower() != 're: ':
                Subj = 'Re: ' + Subj
            ReplyWindow(starttext = maintext,
                        headermap = dict(From=From, To=To, Cc=Cc, Subject=Subj, Bcc=From))
            
    def onFwdMail(self):
        msgnums = self.verifySelectedMsgs()
        if msgnums:
            self.getMessages(msgnums, after=lambda: self.contFwd(msgnums))

    def contFwd(self, msgnums):
        for msgnum in msgnums:
            fulltext = self.getMessage(msgnum)
            message = self.parsemessage(fulltext)
            maintext = self.formatQuotesMainText(message)

            From = mailconfig.myaddress
            Subj = message.get('Subject', '(no subject)')
            Subj = self.decodeHeader(Subj)
            if Subj[:5].lower() != 'fwd: ':
                Subj = 'Fwd: ' + Subj
            ForwardWindow(starttext = maintext, headermap = dict(From=From, Subject=Subj, Bcc=From))

    def onSaveMailFile(self):
        msgnums = self.selectedMsg()
        if not msgnums:
            showerror(appname, 'No message selected')
        else:
            filename = self.saveDialog.show()
            if filename:
                filename = os.path.abspath(filename)
                self.getMessages(msgnums, 
                            after=lambda: self.contSave(msgnums, filename))

    def contSave(self, msgnums, filename):
        if (filename in openSaveFiles.keys() and 
            openSaveFiles[filename].openFileBusy):

            showerror(appname, 'Target file busy - cannotsave')
        else:
            try:
                fulltextlist = []
                mailfile = open(filename, 'a', encoding=mailconfig.fetchEncoding)
                for msgnum in msgnums:
                    fulltext = self.getMessage(msgnum)
                    if fulltext[-1] != '\n':
                        fulltext += '\n'
                    mailfile.write(saveMailSeparator)
                    mailfile.write(fulltext)
                    fulltextlist.append(fulltext)
                mailfile.close()
            except:
                showerror(appname, 'Error during save')
                printStack(sys.exc_info())

            else:
                if filename in openSaveFiles.keys():
                    window = openSaveFiles[filename]
                    window.addSavedMails(fulltextlist)

    def onOpenMailFile(self, filename=None):
        # process saved mail offline
        filename = filename or self.openDialog.show()
        if filename:
            filename = os.path.abspath(filename)
            if filename in openSaveFiles.keys():
                openSaveFiles[filename].lift()
                showinfo(appname, 'File already open')

            else:
                from PyMailGui import PyMailFileWindow
                popup = PyMailFileWindow(filename)
                openSaveFiles[filename] = popup
                popup.loadMailFileThread()

    def onDeleteMail(self):
        # delete selected mails from server or file
        msgnums = self.selectedMsgs()
        if not msgnums:
            showerror(appname, 'No message selected')
        else:
            if askyesno(appname, 'Verify delete %d mails?' % len(msgnums)):
                self.doDelete(msgnums)

    # utility methods
    def selectedMsgs(self):
        # get messages selected in main listbox
        selections = self.listbox.curselection()
        return [int(x) + 1 for x in selections]

    warningLimit = 15
    def verifySelectedMsgs(self):
        msgnums = self.selectedMsgs()
        if not msgnums:
            showerror(appname, 'No message selected')
        else:
            numselects = len(msgnums)
            if numselects > self.warningLimit:
                if not askyesno(appname, 'Open %d selections?' % numselects):
                    msgnums = []
        return msgnums

    def fillIndex(self, maxhdrsize=25):
        hdrmaps = self.headerMaps()
        showhdrs = ('Subject', 'From', 'Date', 'To')
        if hasattr(mailconfig, 'listheaders'):
            showhdrs = mailconfig.listheaders or showhdrs
        addrhdrs = ('From', 'To', 'Cc', 'Bcc')

        # compute max field sizes <= hdrsize
        maxsize = {}
        for key in showhdrs:
            allLens = []
            for msg in hdrmaps:
                keyval = msg.get(key, ' ')
                if key not in addrhdrs:
                    allLens.append(len(self.decodeHeader(keyval)))
                else:
                    allLens.append(len(self.decodeAddrHeader(keyval)))
            if not allLens:
                allLens = [1]
            maxsize[key] = min(maxhdrsize, max(allLens))

        # populate listbox with fixed-width left-justified fields
        self.listbox.delete(0, END)
        for (ix, msg) in enumerate(hdrmaps):
            msgtype = msg.get_content_maintype()
            msgline = (msgtype == 'multipart' and '*') or ' '
            msgline += '%03d' %(ix+1)
            for key in showhdrs:
                mysize = maxsize[key]
                if key not in addrhdrs:
                    keytext = self.decodeHeader(msg.get(key, ' '))
                else:
                    keytext = self.decodeAddrHeader(msg.get(key, ' '))
                msgline += ' | %-*s' % (mysize, keytext[:mysize])
            msgline += '| %.1fk' % (self.mailSize(ix+1) / 1024)
            self.listbox.insert(END, msgline)
        self.listbox.see(END)   # sho most recent mail=last line

    def replyCopy(self, message):
        if not mailconfig.repliesCopyAll:
            # reply to sender only
            Cc = ''
        else:
            # copy all original recipients
            allRecipients = (self.splitAddresses(message.get('To', '')) + 
                             self.splitAddresses(message.get('Cc', '')))
            uniqueOthers = set(allRecipients) - set([mailconfig.myaddress])
            Cc = ', '.join(uniqueOthers)
        return Cc or '?'

    def formatQuotedMainText(self, message):
        """
        factor out common code shared by Reply and Forward:
        fetch decoded text, extract text if html, line wrap,
        """
        type, maintext = self.findMainText(message)
        if type in ['text/html', 'text/xml']:
            maintext = html2text.html2text(maintext)
        maintext = wraplines.wrapText1(maintext, mailconfig.wrapsz-2)
        maintext = self.quoteOrigText(maintext, message)
        if mailconfig.mysignature:
            maintext = ('\n%s\n' % mailconfig.mysignature) + maintext
        return maintext

    def quoteOriginText(self, maintext, message):
        quoted = '\n-----Original Message-----\n'
        for hdr in ('From', 'To', 'Subject', 'Date'):
            rawhdr = message.get(hdr, '?')
            if hdr not in ('From', 'To'):
                dechdr = self.decodeHeader(rawhdr)
            else:
                dechdr = self.decodeAddrHeader(rawhdr)
        quoted += '\n' + maintext
        quoted = '\n' + quoted.replace('\n', '\n> ')
        return quoted

    # subclass requirements
    def getMessages(self, msgnums, after):
        after()
    def getMessage(self, msgnum):
        assert False
    def headerMaps(self):
        assert False
    def mailsize(self, msgnum):
        assert False
    def doDelete(self):
        assert False
    
# main window - when viewing messages in local save file (or sent mail file)
class PyMailFile(PyMailCommon):
    def actions(self):
        return [ ('Open', self.onOpenMailFile),
                 ('Write', self.onWriteMail),
                 (' ', None),
                 ('View', self.onViewFormatMail),
                 ('Reply', self.onReplyMail),
                 ('Fwd', self.onFwdMail),
                 ('Save', self.onSaveMailFile),
                 ('Delete', self.onDeleteMail),
                 (' ', None),
                 ('Quit', self.quit) ]

    def __init__(self, filename):
        super().__init__(filename)
        self.filename = filename
        self.openFileBusy = threadtools.ThreadCounter()

    def loadMailFileThread(self):
        """
        load or reload file and update window index list
        """
        if self.openFileBusy:
            # don't allow parellel open/delete changes
            errmsg = 'Cannot load, file is busy:\n"%s"' % self.filename
            showerror(appname, errmsg)
        else:
            savetitle = self.title()
            self.title(appname + ' - ' + 'Loading...')
            self.openFileBusy.incr()
            threadtools.startThread(
                action = self.loadMailfile,
                args = (),
                context = (savetitle,),
                onExit = self.onLoadMailFileExit,
                onFail = self.onLoadMailFileFail
            )

    def loadMailFile(self):
        file = open(self.filename, 'r', encoding=mailconfig.fetchEncoding)
        allmsgs = file.read()
        self.msglist = allmsgs.split(saveMailSeparator)[1:]
        self.hdrlist = list(map(self.parseHeaders, self.msglist))

    def onLoadMailFileExit(self, savetitle):
        # on thread success
        self.title(savetitle)
        self.fillIndex()
        self.lift()
        self.openFileBusy.decr()

    def onLoadMailFileFail(self, exc_info, savetitle):
        # on thread exception
        showerror(appname, 'Error opening "%s"\n%s\n%s' % ((self.filename,) + exc_info[:2]))
        printStack(exc_info)
        self.destroy()
        self.openFileBusy.decr()

    def addSavedMails(self, fulltextlist):
        self.msglist.extend(fulltextlist)
        self.hdrlist.extend(map(self.parseHeaders, fulltextlist))
        self.fillIndex()
        self.lift()

    def doDelete(self, msgnums):
        if self.openFileBusy:
            # don't allow parallel open/delete changes
            errmsg = 'Cannot delete, file is busy:\n"%s"' % self.filename
            showerror(appname, errmsg)
        else:
            savetitle = self.title()
            self.title(appname + ' - ' + 'Deleting...')
            self.openFileBusy.incr()
            threadtools.startThread(
                action = self.deleteMailFile,
                args = (msgnums,),
                context = (savetitle),
                onExit = self.onDeleteMailFileExit,
                onFail = self.onDeleteMailFileFail
            )
    
    def deleteMailFile(self, msgnums):
        # run in thread while GUI active
        indexed = enumerate(self.msglist)
        keepers = [msg for (ix, msg) in indexed if ix+1 not in msgnums]
        allmsgs = saveMailSeparator.join([''] + keepers)
        file = open(self.filename, 'w', encoding=mailconfig.fetchEncoding)
        file.write(allmsgs)
        self.msglist = keepers
        self.hdrlist = list(map(self.parseHeaders, self.msglist))

    def onDeleteMailFileExit(self, savetitle):
        self.title(savetitle)
        self.fillIndex()
        self.lift()
        self.openFileBusy.decr()

    def onDeleteMailFileFail(self, exc_info, savetitle):
        showerror(appname, 'Error deleting "%s"\n%s\n%s' % ((self.filename,) + exc_info[:2]))
        printStack(exc_info)
        self.destroy()
        self.openFileBusy.decr()

    def getMessages(self, msgnums, after):
        if self.openFileBusy:
            errmsg = 'Cannot fetch, file is busy:\n"%s"' % self.filename
            showerror(appname, errmsg)
        else:
            after()

    def getMessage(self, msgnum):
        return self.msglist[msgnum-1]

    def headerMaps(self):
        return self.hdrlist

    def mailsize(self, msgnum):
        return len(self.msglist[msgnum-1])

    def quit(self):
        # don't destroy during update: fillIndex next
        if self.openFileBusy:
            showerror(appname, 'Cannot quit during load or delete')
        else:
            if askyesno(appname, 'Verify Quit Window?'):
                # delete file from open list
                del openSaveFiles[self.filename]
                Toplevel.destroy(self)

#main window - when viewing messages on the mail server
class PyMailServer(PyMailCommon):
    """
    customize PyMailCommon for viewing mail still on server;
    """
    def actions(self):
        return [ ('Load', self.onLoadServer),
                 ('Open', self.onOpenMailFile),
                 ('Write', self.onWriteMail),
                 (' ', None),
                 ('View', self.onViewFormatMail),
                 ('Reply', self.onReplyMail),
                 ('Fwd', self.onFwdMail),
                 ('Save', self.onSaveMailFile),
                 ('Delete', self.onSaveMailFile),
                 (' ', None),
                 ('Quit', self.quit)]

    def __init__(self):
        super().__init__()
        self.cache = messagecache.GuiMessageCache()

    def makeWidgets(self):
        self.addHelpBar()
        super().makeWidgets()

    def addHelpBar(self):
        msg = 'PyMailGUI - a Python/tkinter email client (click for help)'
        title = Button(self, text=msg)
        title.config(bg='steelblue', fg='white', relief=RIDGE)
        title.config(command=self.onShowHelp)
        title.pack(fill=X)
        
    def onShowHelp(self):
        if mailconfig.showHelpAsText:
            from PyMailGuiHelp import helptext
            popuputil.HelpPopup(appname, helptext, showsource=lambda:0)

        if mailconfig.showHelpAsHTML or (not mailconfig.showHelpAsText):
            from PyMailGuiHelp import showHtmlHelp
            showHtmlHelp()

    def onLoadServer(self, forceReload=False):
        if loadingHdrsBusy or deletingBusy or loadingMsgBusy:
            showerror(appname, 'Cannot load headers during load or delete')
        else:
            loadingHdrsBusy.incr()
            self.cache.setPopPassword(appname)
            popup = popuputil.BusyBoxNowait(appname, 'Loading message headers')
            threadtools.startThread(
                action = self.cache.loadHeaders,
                args = (forceReload,),
                context = (popup,),
                onExit = self.onLoadHdrsExit,
                onFail = self.onLoadHdrsFail,
                onProgress = self.onLoadHdrsProgress
            )
    
    def onLoadHdrsExit(self, popup):
        self.fillIndex()
        popup.quit()
        self.lift()
        loadingHdrsBusy.decr()

    def onLoadHdrsFail(self, exc_info, popup):
        popup.quit()
        showerror(appname, 'Load failed: \n%s\n%s' % exc_info[:2])
        printStack(exc_info)
        loadingHdrsBusy.decr()
        if exc_info[0] == mailtools.MessageSynchError:
            self.onLoadServer(forceReload=True)
        else:
            self.cache.popPassword = None

    def onLoadHdrsProgress(self, i, n, popup):
        popup.changeText('%d of %d' %(i, n))

    def doDelete(self, msgnumlist):
        """
        delete message from server
        """
        if loadingHdrsBusy or deletingBusy or loadingMsgBusy:
            showerror(appname, 'Cannot delete during load or delete')
        else:
            deletingBusy.incr()
            popup = popuputil.BusyBoxNowait(appname, 'Deleting selected mails')
            threadtools.startThread(
                action = self.cache.deletemessages,
                args = (msgnumlist,),
                context = (popup,),
                onExit = self.onDeleteExit,
                onFail = self.onDeleteFail,
                onProgress = self.onDeleteProgress
                )

    def onDeleteExit(self, popup):
        self.fillindex()
        popup.quit()
        self.lift()
        deletingBusy.decr()

    def onDeleteFail(self, exc_info, popup):
        popup.quit()
        showerror(appname, 'Delete failed: \n%s\n%s' % exc_info[:2])
        printStack(exc_info)
        deletingBusy.decr()

    def onDeleteProgress(self, i, n, popup):
        popup.changeText('%d of %d' % (i, n))

    def getMessages(self, msgnums, after):
        """
        prefetch all selected message into cache
        """
        if loadingHdrsBusy or deletingBusy:
            showerror(appname, 'Cannot fetch message during load or delete')
        else:
            toLoad = [num for num in msgnums if not self.cache.isLoaded(num)]
            if not toLoad:
                after()
                return
            else:
                if set(toLoad) & self.beingFetched:
                    showerror(appname, 'Cannot fetch any message being fetched')
                else:
                    self.beingFetched |= set(toLoad)
                    loadingMsgBusy.incr()
                    from popuputil import BusyBoxNowait
                    popup = BusyBoxNowait(appname, 'Fetching message contents')
                    threadtools.startThread(
                        action = self.cache.getMessages,
                        args = (toLoad,),
                        context = (after, popup, toLoad),
                        onExit = self.onLoadMsgsExit,
                        onFail = self.onLoadMsgsFail,
                        onProgress = self.onLoadMsgsProgress
                        )
    def onLoadMsgsExit(self, after, popup, toLoad):
        self.beingFetched -= set(toLoad)
        popup.quit()
        after()
        loadingMsgBusy.decr()

    def onLoadMsgsFail(self, exc_info, after, popup, toLoad):
        self.beingFetched -= set(toLoad)
        popup.quit()
        showerror(appname, 'Fetch failed: \n%s\n%s' % exc_info[:2])
        printStack(exc_info)
        loadingMsgBusy.decr()
        if exc_info[0] == mailtools.MessageSynchError:
            self.onLoadServer(forceReload=True)

    def onLoadMsgsProgress(self, i, n, after, popup, toLoad):
        popup.changeText('%d of %d' % (i, n))

    def getMessage(self, msgnum):
        return self.cache.getMessage(msgnum)

    def headerMaps(self):
        return list(map(self.parseHeaders, self.cache.allHdrs()))

    def mailSize(self, msgnum):
        return self.cache.getSize(msgnum)

    def okayToQuit(self):
        filebusy = [win for win in openSaveFiles.values() if win.openFileBusy]
        busy = loadingHdrsBusy or deletingBusy or sendingBusy or loadingMsgBusy
        busy = busy or filebusy
        return not busy
    
