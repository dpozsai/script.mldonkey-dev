# coding=utf-8
"""
Main class for addon launch
"""

# ===============================================================================
# ###Debugger####
# #REMOTE_DBG = True
# REMOTE_DBG = False
#
# # append pydev remote debugger
# if REMOTE_DBG:
#    # Make pydev debugger works for auto reload.
#    # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
#    try:
#        import pysrc.pydevd as pydevd
#    # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
#        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
#    except ImportError:
#        import sys
#        myerror = ' '.join(sys.path)
#        sys.stderr.write("Error: " +
#            "You must add org.python.pydev.debug.pysrc to your PYTHONPATH." )
#        sys.stderr.write(myerror)
#        sys.exit(1)
# ===============================================================================

import sys
import locale
import xbmcaddon

# import pyxbmct

# Script constants
__addon__ = xbmcaddon.Addon(id='script.mldonkey-dev')
__title__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__language__ = __addon__.getLocalizedString
__cwd__ = __addon__.getAddonInfo('path')


if __name__ == '__main__':
    import resources.lib.view_files as view_files
    import resources.lib.mytools as mytools
    mytools.log("[SCRIPT] '%s: version %s' initialized!" % (__addon__, __version__, ))

    # for other operating systems
    #for lang in locale.locale_alias.values():
    #    mytools.log("Locale languages installed %s" % (lang))
    # get current locale
    loc, enc = locale.getlocale()
    mytools.log("Locale in use: %s Endoding: %s" % (loc, enc))
    prefenc = locale.getpreferredencoding()
    mytools.log("Preferred encoding: %s" % (prefenc))

    window = view_files.GUI(__title__)
    window.doModal()
    # Destroy the instance explicitly because
    # underlying xbmcgui classes are not garbage-collected on exit.
    del window

sys.modules.clear()
