""""""



def statusMessage(self, message, other=None):
    self.statusbar.showMessage(f"{self.condition}   REF:{self.frameref}    {message} : {other}")

    