from SharedNames import *

# message view window - a superclass of write. reply, forward.

class ViewWindow(windows.PopupWindow, mailtools.MailParser):
    """
    A Top level with extra protocol and embedded TextEditor
    """
    # class attributes
    modelabel = 'View'

    from mailconfig import okayToOpenParts      # open any attachments
    from mailconfig import verifyPartOpens      # ask before open
    from mailconfig import maxPartButtons
    from mailconfig import skipTextOnHtmlPart

    tempPartDir = 'TempParts'

    # all view windows use same dialog: remember last dir
    partsDialog = Directory(title=appname + ': Select parts save directory')

    def __init__(self, headermap, showtext, origmessage=None):
        windows.PopupWindow.__init__(self, appname, self.modelabel)
        self.origMessage = origmessage
        self.makeWidgets(headermap, showtext)

    def makeWidgets(self, headermap, showtext):
        actionsframe = self.makeHeaders(headermap)
        if self.origMessage and self.okayToOpenParts:
            self.makePartButtons()
        self.editor = PyNote.TextEditorComponentMinimal(self)
        myactions = self.actionButtons()
        for (label, callback) in myactions:
            b = Button(actionsframe, text=label, command=callback)
            b.config(bg='beige', relief=RIDGE, bd=2)
            b.pack(side=TOP, expand=YES, fill=BOTH)

        # body text, pack last=clip first
        self.editor.pack(side=BOTTOM)
        self.update()
        self.editor.setAllText(showtext)
        lines = len(showtext.splitlines())
        lines = min(lines+3, mailconfig.viewheight or 20)
        self.editor.setHeight(lines)
        self.editor.setWidth(80)
        if mailconfig.viewbg:
            self.editor.setBg(mailconfig.viewbg)
        if mailconfig.viewfg:
            self.editor.setFg(mailconfig.viewfg)
        if mailconfig.viewfont:
            self.editor.setFont(mailconfig.viewfont)

    def makeHeaders(self, headermap):
        top = Frame(self); top.pack(side=TOP, fill=X)
        left = Frame(top); left.pack(side=LEFT, expand=NO, fill=BOTH)
        middle = Frame(top); middle.pack(side=LEFT, expand=YES, fill=X)

        self.userHdrs = ()
        showhdrs = ('From', 'To', 'Cc', 'Subject')
        if hasattr(mailconfig, 'viewheaders') and mailconfig.viewheaders:
            self.userHdrs = mailconfig.viewheaders
            showhdrs += self.userHdrs
        addrhdrs = ('From', 'To', 'Cc', 'Bcc')
        self.hdrFields = []
        for (i, header) in enumerate(showhdrs):
            lab = Label(middle, text=header+':', justify=LEFT)
            ent = Entry(middle)
            lab.grid(row=i, column=0, sticky=EW)
            ent.grid(row=i, column=1, sticky=EW)
            middle.rowconfigure(i, weight=1)
            hdrvalue = headermap.get(header, '?')
            
            if header not in addrhdrs:
                hdrvalue = self.decodeHeader(hdrvalue)
            else:
                hdrvalue = self.decodeAddrHeader(hdrvalue)
            ent.insert('0', hdrvalue)
            self.hdrFields.append(ent)
        middle.columnconfigure(1, weight=1)
        return left

    def actionButtons(self):
        return [('Cancel', self.destroy),
                ('Parts', self.onParts),
                ('Split', self.onSplit)]

    def makePartButtons(self):
        def makeButton(parent, text, callback):
            link = Button(parent, text=text, command=callback, relief=SUNKEN)
            if mailconfig.partfg:
                link.config(fg=mailconfig.partfg)
            if mailconfig.partbg:
                link.config(bg=mailconfig.partbg)
            link.pack(side=LEFT, fill=X, expand=YES)
        parts = Frame(self)
        parts.pack(side=TOP, expand=NO, fill=X)
        for (count, partname) in enumerate(self.partsList(self.origMessage)):
            if count == self.maxPartButtons:
                makeButton(parts, '...', self.onSplit)
                break
            openpart = (lambda partname=partname: self.onOnePart(partname))
            makeButton(parts, partname, openpart)

    def onOnePart(self, partname):
        """
        locate selceted part for button and save and open;
        """
        try:
            savedir = self.tempPartDir
            message = self.origMessage
            (contype, savepath) = self.saveOnePart(savedir, partname, message)
        except:
            showerror(appname, 'Error while writing part file')
            printStack(sys.exc_info())
        else:
            self.openParts([(contype, os.path.abspath(savepath))])

    def onParts(self):
        """
        show message part/attachment in pop up window;
        """
        partnames = self.partsList(self.origMessage)
        msg =  '\n'.join(['Message parts:\n'] + partnames)
        showinfo(appname, msg)

    def onSplit(self):
        """
        pop up save dir dialog and save all parts/attachments there;
        """
        savedir = self.partsDialog.show()
        if savedir:
            try:
                partfiles = self.saveParts(savedir, self.origMessage)
            except:
                showerror(appname, 'Error while writing part files')
                printStack(sys.exc_info())
            else:
                if self.okayToOpenParts:
                    self.openParts(partfiles)
    
    def askOpen(self, appname, prompt):
        if not self.verifyPartOpens:
            return True
        else:
            return askyesno(appname, prompt)

    def openParts(self, partfiles):
        def textPartEncoding(fullfilename):
            partname = os.path.basename(fullfilename)
            for (filename, contype, part) in self.walkNamedParts(self.origMessage):
                if filename == partname:
                    return part.get_content_charset()
            assert False, 'Text part not found'
    
        for (contype, fullfilename) in partfiles:
            maintype = contype.split('/')[0]
            extension = os.path.splitext(fullfilename)[1]
            basename = os.path.basename(fullfilename)

            # HTML and XML text, web pages, some media
            if contype in ['text/html', 'text/xml']:
                browserOpened = False
                if self.askOpen(appname, 'Open "%s" in browser?' % basename):
                    try:
                        webbrowser.open_new('file://' + fullfilename)
                        browserOpened = True
                    except:
                        showerror(appaname, 'Browser failed: trying editor')
                
                if not browserOpened or not self.skipTextOnHtmlPart:
                    try:
                        # try PyNote to see encoding name and effect
                        encoding = textPartEncoding(fullfilename)
                        PyNote.TextEditorMainPopup(parent=self,
                                loadFirst=fullfilename, loadEncoding=encoding)
                    except:
                        showerror(appname, 'Error opening text viewer')

            # text/plain, text/x-python
            elif maintype == 'text':
                if self.askOpen(appname, 'open text part "%s"?' % basename):
                    try:
                        encoding = textPartEncoding(fullfilename)
                        PyNote.TextEditorMainPopup(parent=self,
                                loadFirst=fullfilename, loadEncoding=encoding)
                    except:
                        showerror(appname, 'Error opening text viewer')

            #multimedia types
            elif maintype in ['image', 'audio', 'video']:
                if self.askOpen(appname, 'Open media part "%s"?' % basename):
                    try:
                        webbrowser.open_new('file://' + fullfilename)
                    except:
                        showerror(appname, 'Error opening browser')
            
            #common windows documents
            elif (sys.platform[:3] == 'win' and 
                maintype == 'application' and 
                extension in ['.doc', '.docx', '.xls', '.xlsx', 
                              '.pdf', '.zip', '.tar', '.wmv']
                ):
                if self.askOpen(appname, 'Open part "%s"?' % basename):
                    os.startfile(fullfilename)

            else:
                msg = 'Cannot open part: "%s"\nOpen manually in: "%s"'
                msg = msg % (basename, os.path.dirname(fullfilename))
                showinfo(appname, msg)

if mailconfig.smtpuser:
    MailSenderClass = mailtools.MailSenderAuth
else:
    MailSenderClass = mailtools.MailSender

class WriteWindow(ViewWindow, MailSenderClass):
    modelabel = 'Write'

    def __init__(self, headermap, starttext):
        ViewWindow.__init__(self, headermap, starttext)
        MailSenderClass.__init__(self)
        self.attaches = []
        self.openDialog = None

    def actionButtons(self):
        return [('Cancel', self.quit),
                ('Parts', self.onParts),
                ('Attach', self.onAttach),
                ('Send', self.onSend)]

    def onParts(self):
        if not self.attaches:
            showinfo(appname, 'Nothing attached')
        else:
            msg = '\n'.join(['Already attached:\n'] + self.attaches)
            showinfo(appname, msg)
        
    def onAttach(self):
        """
        Attach file to the mail.
        """
        if not self.openDialog:
            self.openDialog = Open(title=appname + ': Select Attachment File')
        filename = self.openDialog.show()
        if filename:
            self.attaches.append(filename)

    def resolveUnicodeEncodings(self):
        def isTextKind(filename):
            contype, encoding = mimetypes.guess_type(filename)
            if contype is None or encoding is not None:
                return False
            maintype, subtype = contype.split('/', 1)
            return maintype == 'text'

        # resolve many body text encoding
        bodytextEncoding = mailconfig.mainTextEncoding
        if bodytextEncoding == None:
            asknow = askstring('PyMailGui', 'Enter main text unicode encoding name')
            bodytextEncoding = asknow or 'latin-1'

        # use utf-8 if can't encode per prior selections
        if bodytextEncoding != 'utf-8':
            try:
                bodytext = self.editor.getAllText()
                bodytext.encode(bodytextEncoding)
            except (UnicodeError, LookupError):
                bodytextEncoding = 'utf-8'

        # resolve any text part attachment encodings
        attachesEncodings = []
        config = mailconfig.attachmentTextEncoding
        for filename in self.attaches:
            if not isTextKind(filename):
                attachesEncodings.append(None)
            elif config != None:
                attachesEncodings.append(config)
            else:
                prompt = 'Enter Unicode encoding name for %s' % filename
                asknow = askstring('PyMailGui', prompt)
                attachesEncodings.append(asknow or 'latin-1')

            # use utf-8 if can't decode per prior selections
            choice = attachesEncodings[-1]
            if choice != None and choice != 'utf-8':
                try:
                    attachbytes = open(filename, 'rb').read()
                    attachbytes.decode(choice)
                except (UnicodeError, LookupError):
                    attachesEncoding[-1] = 'utf-8'
        return bodytextEncoding, attachesEncodings

    def onSend(self):
        """send button callback handler"""
        #resolve unicode encoding for text parts;
        bodytextEncoding, attachesEncodings = self.resolveUnicodeEncodings()

        # get components from GUI
        fieldvalues = [entry.get() for entry in self.hdrFields]
        From, To, Cc, Subj = fieldvalues[:4]
        extraHdrs = [('Cc', Cc), ('X-Mailer', appname + '(Python)')]
        extraHdrs += list(zip(self.userHdrs, fieldvalues[4:]))
        bodytext = self.editor.getAllText()

        # split multiple reciepent lists on ',', fix empty fields
        Tos = self.splitAddresses(To)
        for (ix, (name, value)) in enumerate(extraHdrs):
            if value:
                if value == '?':
                    extraHdrs[ix] = (name, '')
                elif name.lower() in ['cc', 'bcc']:
                    extraHdrs[ix] = (name, self.splitAddresses(value))

        # withdraw to disallow send duriing send
        self.withdraw()
        self.getPassword()
        popup = popuputil.BusyBoxNowait(appname, 'Sending message')
        sendingBusy.incr()
        threadtools.startThread(
            action = self.sendMessage,
            args = (From, Tos, Subj, extraHdrs, bodytext, self.attaches, saveMailSeparator, bodytextEncoding, attachesEncodings),
            context = (popup,),
            onExit = self.onSendExit,
            onFail = self.onSendFail
        )

    def onSendExit(self, popup):
        popup.quit()
        self.destroy()
        sendingBusy.decr()

        sentname = os.path.abspath(mailconfig.sentmailfile)
        if sentname in openSaveFiles.keys():
            window = openSaveFiles[sentname]
            window.loadMailFileThread()

    def onSendFail(self, exc_info, popup):
        popup.quit()
        self.deiconify()
        self.lift()
        showerror(appname, 'Send failed: \n%s\n%s' % exc_info[:2])
        printStack(exc_info)
        MailSenderClass.smtpPassword = None
        sendingBusy.decr()

    def askSmtpPassword(self):
        password = ''
        while not password:
            prompt = ('Password for %s on %s?' % (self.smtpUser, self.smtpServerName))
            password = popuputil.askPasswordWindow(appname, prompt)
            return password

class ReplyWindow(WriteWindow):
    """
    customize write display for replying
    text and headers set up by list window
    """
    modelabel = 'Reply'

class ForwardWindow(WriteWindow):
    """
    customize write display for forwading
    text and headers set up by list window
    """
    modelabel = 'Forward'