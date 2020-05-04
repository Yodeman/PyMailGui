from p_python.internet.Email import mailtools
from popuputil import askPasswordWindow

class MessageInfo:
    """
    an item in the mail cache list
    """
    def __init__(self, hdrtext, size):
        self.hdrtext = hdrtext
        self.fullsize = size
        self.fulltext = None

class MessageCache(mailtools.MailFetcher):
    def __init__(self):
        super().__init__()
        self.msglist = []

    def loadHeaders(self, forceReloads, progress=None):
        """
        initial full load, load newly arrived and 
        forced reload after delete
        """
        if forceReloads:
            loadfrom = 1
            self.msglist = []
        else:
            loadfrom = len(self.msglist)+1

        # only if loading newly arrived
        if loadfrom != 1:
            self.checkSynchError(self.allHdrs())

        # get all or newly arrived
        reply = self.downloadAllHeaders(progress, loadfrom)
        headersList, msgSizes, loadedFull = reply

        for (hdrs, size) in zip(headersList, msgSizes):
            newmsg = MessageInfo(hdrs, size)
            if loadedFull:
                newmsg.fulltext = hdrs
            self.msglist.append(newmsg)

    def getMessage(self, msgnum):
        cacheobj = self.msglist[msgnum-1]
        if not cacheobj.fulltext:
            fulltext = self.downloadMessage(msgnum)
            cacheobj.fulltext = fulltext
        return cacheobj.fulltext

    def getMessages(self, msgnums, progress=None):
        self.checkSynchError(self.allHdrs())
        nummsgs = len(msgnums)
        for (ix, msgnum) in enumerate(msgnums):
            if progress:
                progress(ix+1, nummsgs)
            self.getMessage(msgnum)

    def getSize(self, msgnum):
        return self.msglist[msgnum-1].fullsize

    def isLoaded(self, msgnum):
        return self.msglist[msgnum-1].fulltext

    def allHdrs(self):
        return [msg.hdrtext for msg in self.msglist]

    def deleteMessages(self, msgnums, progress=None):
        try:
            self.deleteMessagesSafely(msgnums, self.allHdrs(), progress)
        except:
            mailtools.MailFetcher.deleteMessages(self, msgnums, progress)
        
        # if no error: update index list
        indexed = enumerate(self.msglist)
        self.msglist = [msg for (ix, msg) in indexed if ix+1 not in msgnums]

class GuiMessageCache(MessageCache):
    def setPopPassword(self, appname):
        """
        get password from GUI main thread,
        forceably called from GUI to avoid pop ups in threads.
        """
        if not self.popPassword:
            prompt = 'Passord for %s on %s?' % (self.popUser, self.popServer)
            self.popPassword = askPasswordWindow(appname, prompt)

    def askPopPassword(self):
        return self.popPassword
