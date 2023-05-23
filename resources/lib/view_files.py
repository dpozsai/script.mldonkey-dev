# coding=utf-8
"""view_files is the main module used for different windows.

Returns:
    Nothing
"""
from __future__ import unicode_literals

import os
import sys
import telnetlib

import xbmc
import xbmcgui
import xbmcvfs

import pyxbmct
from . import mytools

###Debug
import web_pdb
#web_pdb.set_trace()

#enable localization
getLS = sys.modules["__main__"].__language__
__cwd__ = sys.modules["__main__"].__cwd__
__addon__ = sys.modules["__main__"].__addon__

_check_icon_ = os.path.join(__cwd__, "resources/media/blue-icon.png")
_media_icon_ = os.path.join(__cwd__, "resources/media")

__folderSize__ = 25
__downloadedSize__ = 80
__destinationSize__ = 50
__sourceSize__ = 50

#Actions used
ACTION_MOVE_UP = 3
ACTION_MOVE_DOWN = 4


# def log(txt):
#     """Log string to Kodi with DEBUG level.

#     Args:
#         txt (str): String that will be sent to log
#     """
#     xbmc.log(msg=txt, level=xbmc.LOGDEBUG)

class GUI(pyxbmct.AddonDialogWindow):
    """Main Window - Shows downloaded files.

    Child of pyxbmct.AddonDialogWindow

    Args:
        title (str, optional): Header of window. Defaults to ''.

    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, title=''):
        """GUI Constructor

        Args:
            title (str, optional): Header of window. Defaults to ''.
        """
        super(GUI, self).__init__(title)
        self.setGeometry(1180, 620, 13, 4)
        self.define_controls()
        self.place_controls()
        self.actions()
        self.load_list()
        self.set_navigation()
        # Connect a key action (Backspace) to close the window.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

    def define_controls(self):
        """Create controls.
        """
        self.tab_downloaded = pyxbmct.Button(getLS(30001))
        self.downloading_tab = pyxbmct.Button(getLS(30003))
        self.exceptions_tab = pyxbmct.Button(getLS(30002))
        self.list = pyxbmct.List(
            _imageWidth=30, _imageHeight=30, _itemTextXOffset=0)
        self.library_button = pyxbmct.Button(getLS(30004))
        self.exception_button = pyxbmct.Button(getLS(30005))
        self.remove_button = pyxbmct.Button(getLS(30006))
        self.exit_button = pyxbmct.Button(getLS(30099))
        self.pattern_button = pyxbmct.Button(getLS(30061))

    def place_controls(self):
        """Place controls in window.
        """
        self.placeControl(self.tab_downloaded, 0, 0)
        self.placeControl(self.downloading_tab, 0, 1)
        self.placeControl(self.exceptions_tab, 0, 2)
        self.placeControl(self.list, 1, 0, 12, 3)
        self.placeControl(self.library_button, 2, 3, 2, 1)
        self.placeControl(self.exception_button, 5, 3, 2, 1)
        self.placeControl(self.remove_button, 8, 3, 2, 1)
        self.placeControl(self.exit_button, 12, 0, 1, 3)
        self.placeControl(self.pattern_button, 0, 3)

    def set_navigation(self):
        """Set navigation between controls.
        """
        self.list.setNavigation(self.tab_downloaded, self.exit_button,
                                self.library_button, self.library_button)
        self.tab_downloaded.setNavigation(self.exit_button, self.list,
                                          self.pattern_button, self.downloading_tab)
        self.downloading_tab.setNavigation(self.exit_button, self.list,
                                           self.tab_downloaded, self.exceptions_tab)
        self.exceptions_tab.setNavigation(self.exit_button, self.list,
                                          self.downloading_tab, self.pattern_button)
        self.library_button.setNavigation(self.pattern_button, self.exception_button, self.list, self.list)
        self.exception_button.setNavigation(self.library_button, self.remove_button, self.list, self.list)
        self.remove_button.setNavigation(self.exception_button, self.exit_button, self.list, self.list)
        self.exit_button.controlUp(self.list)
        self.exit_button.controlDown(self.tab_downloaded)
        self.pattern_button.setNavigation(self.remove_button, self.library_button, self.exceptions_tab, self.tab_downloaded)
        # Set initial focus
        self.setFocus(self.list)

    def actions(self):
        """Link active controls with actions.
        """
        self.connect(self.exit_button, self.close)
        self.connect(self.list, self.check_uncheck)
        self.connect(self.library_button, self.library_action)
        self.connect(self.exception_button, self.add_exceptions)
        self.connect(self.remove_button, self.remove_files)
        self.connect(self.exceptions_tab, self.manage_exceptions)
        self.connect(self.downloading_tab, self.show_downloading)
        self.connect(self.tab_downloaded, self.load_list)
        self.connect(self.pattern_button, self.show_pattern)

    def load_list(self):
        """Load Downloaded view with files.
        """
        self.list.reset()
        mytools.log("Entering load_list")
        self.ficheros = mytools.list_files()
        # self.ficheros = self.file_list.ficheros
        mytools.log("ficheros %s" % (" ".join(self.ficheros)))
        progress_dialog = xbmcgui.DialogProgress()
        progress_dialog.create(getLS(30025), getLS(30026))
        leido = 0
        for fichero in self.ficheros:
            leido = leido+1
            progress_dialog.update(
                int (100*leido/(leido+len(self.ficheros))), getLS(30026) + " " + fichero)
            mytools.log("Each file %s" % (fichero))
            self.list.addItem(mytools.shorten_file(
                __downloadedSize__, fichero))
            self.list.getListItem(self.list.size()-1).setProperty('File', fichero)
        if self.list.size() == 0:
            self.list.addItem("")

    def check_uncheck(self):
        """Toggles listItem status and set icon.
        """
        list_item = self.list.getSelectedItem()
        if list_item.getProperty('Checked') == "True":
            list_item.setArt({'icon' : ""})
            list_item.setProperty('Checked', "False")
        else:
            list_item.setArt({'icon': _check_icon_})
            list_item.setProperty('Checked', "True")

    def library_action(self):
        """Deliver selected files to new window.
        """
        # self.selected = [index for index in xrange(self.listing.size())
        # if self.listing.getListItem(index).getProperty('Checked') == "True"]
        selected = []
        all_items = []
        for i in range(0, self.list.size()):
            all_items.append(self.list.getListItem(i).getProperty('File'))
            if self.list.getListItem(i).getProperty('Checked') == "True":
                selected.append(self.list.getListItem(i).getProperty('File'))
        if len(selected) == 0:
            selected = all_items
        window = GUILibrary("", selected, self)
        window.doModal()
        # Destroy the instance explicitly because
        # underlying xbmcgui classes are not garbage-collected on exit.
        del window

    def setAnimation(self, control):
        """Set fade animation for all add-on window controls.
        """
        control.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=500', ),
                               ('WindowClose', 'effect=fade start=100 end=0 time=500', )])

    def add_exceptions(self):
        """Add selected files to exception list
        """
        selected = []
        for i in range(0, self.list.size()):
            if self.list.getListItem(i).getProperty('Checked') == "True":
                selected.append(self.list.getListItem(i).getProperty('File'))
        if len(selected) == 0:
            xbmcgui.Dialog().ok(getLS(30050), getLS(30051))
        elif xbmcgui.Dialog().yesno(getLS(30010), getLS(30011), getLS(30012)):
            mytools.Exceptions().add_exceptions(selected)
            self.load_list()

    def remove_files(self):
        """Call method to remove selected files.
        """
        #TODO remove files from disk. Ask for confirmation, only allow for selected files.
        # pass

    def manage_exceptions(self):
        """Open exceptions windows
        """
        window = GUIFilter(title=getLS(30029))
        window.doModal()
        # Destroy the instance explicitly because
        # underlying xbmcgui classes are not garbage-collected on exit.
        del window
        self.close()

    def show_downloading(self):
        """Open MLDonkey current download view
        """
        window = GuiMLdonkey(title=getLS(30080))
        window.doModal()
        # Destroy the instance explicitly because
        # underlying xbmcgui classes are not garbage-collected on exit.
        del window
        self.close()

    def show_pattern(self):
        """Open MLDonkey current download view
        """
        window = GUIPattern(title=getLS(30062))
        window.doModal()
        # Destroy the instance explicitly because
        # underlying xbmcgui classes are not garbage-collected on exit.
        del window
        self.close()


class GuiMLdonkey(pyxbmct.AddonDialogWindow):
    """Show downloaed files

    Usage:
        window = GUI_MLdonkey(title=getLS(30080))
        window.doModal()
        del window
    """
    # TODO Implementar mas funciones con boton drecho sobre una fila.
    # Priorizar pause / delete. Luego cambiar prioridad y obtener info.
    def __init__(self, title=''):
        """[summary]

        Args:
            title (str, optional): Window header. Defaults to ''.
        """
        super(GuiMLdonkey, self).__init__(title)
        self.setGeometry(1180, 620, 16, 4)
        self.define_controls()
        self.place_controls()
        self.actions()
        self.load_list()
        self.set_navigation()
        # Connect a key action (Backspace) to close the window.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

    def define_controls(self):
        """Create controls.
        """
        self.tab_downloaded = pyxbmct.Button(getLS(30001))
        self.downloading_tab = pyxbmct.Button(getLS(30003))
        self.exceptions_tab = pyxbmct.Button(getLS(30002))
        self.info = pyxbmct.FadeLabel(font="Mono26")
        self.header = pyxbmct.Label("", font="Mono26")
        self.list = pyxbmct.List(
            font="Mono26", _imageWidth=30, _imageHeight=30, _itemTextXOffset=0)
        self.ok_button = pyxbmct.Button(getLS(30009))

    def place_controls(self):
        """Place controls in window.
        """
        self.placeControl(self.tab_downloaded, 0, 0)
        self.placeControl(self.downloading_tab, 0, 1)
        self.placeControl(self.exceptions_tab, 0, 2)
        self.placeControl(self.info, 1, 0, 1, 4)
        self.placeControl(self.header, 2, 0, 1, 4)
        self.placeControl(self.list, 3, 0, 13, 4)
        self.placeControl(self.ok_button, 15, 0, 1, 3)

    def set_navigation(self):
        """Set navigation between controls.
        """
        self.tab_downloaded.setNavigation(self.ok_button, self.list, self.exceptions_tab, self.downloading_tab)
        self.downloading_tab.setNavigation(self.ok_button, self.list, self.tab_downloaded, self.exceptions_tab)
        self.exceptions_tab.setNavigation(self.ok_button, self.list, self.downloading_tab, self.tab_downloaded)
        self.ok_button.controlUp(self.list)
        self.ok_button.controlDown(self.tab_downloaded)
        self.list.controlUp(self.tab_downloaded)
        self.list.controlDown(self.ok_button)
        # Set initial focus
        self.setFocus(self.list)

    def actions(self):
        """Link active controls with actions.
        """
        self.connect(self.ok_button, self.show_downloaded)
        self.connect(self.exceptions_tab, self.manage_exceptions)
        self.connect(self.downloading_tab, self.load_list)
        self.connect(self.tab_downloaded, self.show_downloaded)

    def load_list(self):
        """Load MLDonkey results
        """
        self.list.reset()
        downloaded = self.MLdonkey("vd")
        downloaded = downloaded.split("\x1B")
        # result = []
        label = "    {0:<4}{1:^49}{2:>11}{3:>11}/{4:<9}{5:^9}{6:^9}".format(getLS(
            30081), getLS(30014), getLS(30082), getLS(30083), getLS(30084), getLS(30085), getLS(30086))
        mytools.log(label)
        # self.header.setLabel("    {0:<4}{1:^49}{2:>11}{3:>11}/{4:<9}{5:^9}{6:^9}".format(getLS(
        #     30081), getLS(30014), getLS(30082), getLS(30083), getLS(30084), getLS(30085), getLS(30086)))
        self.header.setLabel(label)
        # self.list.addItem('1234567890123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|')
        for line in downloaded:
            line.strip()
            line = line.partition("m")
            line = line[2]
            # log("LINE: %s" %(line))
            if line.startswith("["):
                line = line.split()
                line_size = len(line)
                MLnetwork = line[0].replace("[", "")
                MLnumber = line[1].replace("]", "")
                MLRele = line[2]
                MLComm = line[3]
                MLUser = line[4]
                MLGroup = line[5]
                MLFile = " ".join([line[x]
                                   for x in range(6, line_size-8)]).strip()
                MLPerc = line[line_size-8]
                MLDone = line[line_size-7]
                MLSize = line[line_size-6]
                MLlSeen = line[line_size-5]
                MLOld = line[line_size-4]
                MLActive = line[line_size-3]
                MLRate = line[line_size-2]
                MLPrio = line[line_size-1]

                self.list.addItem("{0:<3}{1:*<50}{2:>10}%{3:>12}/{4:<9}{5:^9}{6:^9}\n".format(
                    MLPrio, MLFile, MLPerc, MLDone, MLSize, MLOld, MLRate))
                self.list.getListItem(self.list.size()-1).setProperties({'network': MLnetwork,
                                                                         'number': MLnumber, 'Rele': MLRele, 'Comm': MLComm,
                                                                         'User': MLUser, 'Group': MLGroup, 'File': MLFile,
                                                                         'Perc': MLPerc, 'Done': MLDone, 'Size': MLSize,
                                                                         'lSeen': MLlSeen, 'Old': MLOld, 'Active': MLActive,
                                                                         'Rate': MLRate, 'Prio': MLPrio})
                if MLnetwork == "D":
                    self.list.getListItem(
                        self.list.size()-1).setArt({'icon': os.path.join(_media_icon_, "edonkey.png")})
                elif MLnetwork == "B":
                    self.list.getListItem(
                        self.list.size()-1).setArt({'icon': os.path.join(_media_icon_, "bittorrent.png")})
                else:
                    self.list.getListItem(
                        self.list.size()-1).setArt({'icon': os.path.join(_media_icon_, "question.png")})
            elif line.startswith("\n"):
                line = line.strip()
                if not line.startswith(">"):
                    self.info.reset()
                    self.info.addLabel(line.strip())
                    # log("INFOLINE: %s" %(line.strip()))
            elif line.startswith("Num"):
                line = line.split()
                line_size = len(line)
                # log("HEADERLINE: %s" %("|".join([line[x] for x in range(lineSize)])) )
            else:
                continue

    def MLdonkey(self, command):
        """Connect to MLdonkey

        Args:
            command (str): The command sent to MLDonkey server.

        Returns:
            string: full result from telnet.
        """
        command = command + "\n"
        command = command.encode('ascii')
        MLServer = __addon__.getSetting("MLdonkey_IP")
        MLPort = int(__addon__.getSetting("MLdonkey_port"))
        MLauth = __addon__.getSetting(
            "MLdonkey_auth").lower() in ("true", "yes")
        MLuser = __addon__.getSetting("MLdonkey_user")
        MLpass = __addon__.getSetting("MLdonkey_passwd")

        MLDk = telnetlib.Telnet(MLServer, MLPort)

        if MLauth:
            MLDk.read_until("login :".encode('ascii'))
            MLDk.write(MLuser + "\n".encode('ascii'))
            MLDk.read_until("Password: ".encode('ascii'))
            MLDk.write(MLpass + "\n".encode('ascii'))
        MLDk.read_until(">".encode('ascii'), 100)
        MLDk.write(command)

        MLDk.write("exit\n".encode('ascii'))

        result = MLDk.read_all().decode('utf-8')
        return result

    def manage_exceptions(self):
        """Go to Exceptions window.
        """
        window = GUIFilter(title=getLS(30029))
        window.doModal()
        # Destroy the instance explicitly because
        # underlying xbmcgui classes are not garbage-collected on exit.
        del window
        self.close()

    def show_downloaded(self):
        """Go to downloaded window.
        """
        window = GUI(title=getLS(30000))
        window.doModal()
        # Destroy the instance explicitly because
        # underlying xbmcgui classes are not garbage-collected on exit.
        del window
        self.close()


class GUIFilter(pyxbmct.AddonDialogWindow):
    """Filter Window - Shows files, directories and extensions.

    Child of pyxbmct.AddonDialogWindow
    TODO define better inheritance - should be son of GUI
    Args:
        title (str, optional): Header of window. Defaults to ''.

    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, title=''):
        """GUI_Filter constructor

        Args:
            title (str, optional): Defaults to ''.
        """
        super(GUIFilter, self).__init__(title)
        self.setGeometry(1180, 620, 16, 7)
        self.define_controls()
        self.place_controls()
        self.actions()
        self.load_list()
        self.set_navigation()
        # Connect a key action (Backspace) to close the window.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
        self.current_tab = 'file'

    def define_controls(self):
        """Defines controls.
        """
        self.tab_downloaded = pyxbmct.Button(getLS(30001))
        self.downloading_tab = pyxbmct.Button(getLS(30003))
        self.exceptions_tab = pyxbmct.Button(getLS(30002))
        self.files_button = pyxbmct.Button(getLS(30030))
        self.directories_button = pyxbmct.Button(getLS(30031))
        self.extensions_button = pyxbmct.Button(getLS(30032))
        self.disklookup_button = pyxbmct.Button(getLS(30033))
        self.disable_button = pyxbmct.Button(getLS(30034))
        self.remove_button = pyxbmct.Button(getLS(30035))
        self.info = pyxbmct.Label(getLS(30037))
        self.list = pyxbmct.List(_imageWidth=20, _imageHeight=20, _itemTextXOffset=0)
        self.back_button = pyxbmct.Button(getLS(30009))

    def place_controls(self):
        """Place controls.
        """
        self.placeControl(self.tab_downloaded, 0, 0, 1, 2)
        self.placeControl(self.downloading_tab, 0, 2, 1, 2)
        self.placeControl(self.exceptions_tab, 0, 4, 1, 2)
        self.placeControl(self.info, 1, 0, 1, 7)
        self.placeControl(self.files_button, 2, 0, 1, 2)
        self.placeControl(self.directories_button, 2, 2, 1, 2)
        self.placeControl(self.extensions_button, 2, 4, 1, 2)
        self.placeControl(self.list, 3, 0, 13, 6)
        self.placeControl(self.back_button, 15, 0, 1, 6)
        self.placeControl(self.disklookup_button, 3, 6, 2, 1)
        self.placeControl(self.disable_button, 6, 6, 2, 1)
        self.placeControl(self.remove_button, 9, 6, 2, 1)

    def set_navigation(self):
        """Define how button navigation is done.
        """
        self.tab_downloaded.setNavigation(self.back_button, self.files_button, self.exceptions_tab, self.downloading_tab)
        self.downloading_tab.setNavigation(self.back_button, self.files_button, self.tab_downloaded, self.exceptions_tab)
        self.exceptions_tab.setNavigation(self.back_button, self.files_button, self.downloading_tab, self.tab_downloaded)
        self.back_button.controlUp(self.list)
        self.back_button.controlDown(self.tab_downloaded)
        self.list.setNavigation(self.files_button, self.back_button, self.disklookup_button, self.disklookup_button)
        self.files_button.setNavigation(self.tab_downloaded, self.list, self.extensions_button, self.directories_button)
        self.directories_button.setNavigation(self.tab_downloaded, self.list, self.files_button, self.extensions_button)
        self.extensions_button.setNavigation(self.tab_downloaded, self.list, self.directories_button, self.files_button)
        self.disklookup_button.setNavigation(self.remove_button, self.disable_button, self.list, self.list)
        self.disable_button.setNavigation(self.disklookup_button, self.remove_button, self.list, self.list)
        self.remove_button.setNavigation(self.disable_button, self.disklookup_button, self.list, self.list)
        # Set initial focus
        self.setFocus(self.files_button)

    def actions(self):
        """Connect controls with actions.
        """
        self.connect(self.back_button, self.show_downloaded)
        self.connect(self.exceptions_tab, self.load_list)
        self.connect(self.downloading_tab, self.show_downloading)
        self.connect(self.tab_downloaded, self.show_downloaded)
        self.connect(self.directories_button, lambda: self.load_list('directory'))
        self.connect(self.extensions_button, lambda: self.load_list('extension'))
        self.connect(self.files_button, lambda: self.load_list('file'))
        self.connect(self.disklookup_button, self.disk_lookup)
        self.connect(self.disable_button, self.disable_enable)
        self.connect(self.remove_button, self.remove_entries)
        self.connect(self.list, self.check_uncheck)

    def load_list(self, exception_type='file'):
        """Reloads list from current tab.

        Args:
            exception_type (str, optional): File that indicates current tab [file|directory|exception]. Defaults to 'file'.
        """
        self.listado_excepciones = mytools.Exceptions(exception_type).list_exceptions()
        self.list.reset()
        for item in self.listado_excepciones:
            self.list.addItem(item)
            self.list.getListItem(self.list.size()-1).setProperty('File', item)
            if item.startswith("!"):
                self.list.getListItem(self.list.size()-1).setLabel("[COLOR grey][I]" + item + "[/I][/COLOR]")
        self.current_tab = exception_type
        disk_button_label = {'file': 30033,
                             'directory': 30033, 'extension': 30036}
        type_label = {'file': 30037, 'directory': 30038, 'extension': 30039}
        self.info.setLabel(getLS(type_label[exception_type]))
        self.disklookup_button.setLabel(
            getLS(disk_button_label[exception_type]))
        if self.list.size() == 0:
            self.list.addItem("")

    def check_uncheck(self):
        """Check or uncheck list items.
        """
        list_item = self.list.getSelectedItem()
        if list_item.getProperty('Checked') == "True":
            list_item.setArt({'icon': ""})
            list_item.setProperty('Checked', "False")
        else:
            list_item.setArt({'icon': _check_icon_})
            list_item.setProperty('Checked', "True")

    def disk_lookup(self):
        """Open file dialog to add new file or directory or and new text entry in exceptions list.
        """
        #TODO revisar - no tengo claro que este bien
        selected = []
        if self.current_tab == 'directory':
            selected.append(xbmcgui.Dialog().browse(0, getLS(30040), 'files', '', False, False, __addon__.getSetting("folder")))
            try:
                i = selected.index(__addon__.getSetting("folder"))
            except:
                mytools.Exceptions(self.current_tab).add_exceptions(selected)
        elif self.current_tab == 'file':
            selected.append(xbmcgui.Dialog().browse(1, getLS(30041), 'files', '', False, False, __addon__.getSetting("folder")))
            try:
                i = selected.index(__addon__.getSetting("folder"))
            except:
                mytools.Exceptions(self.current_tab).add_exceptions(selected)
        elif self.current_tab == 'extension':
            keybd = xbmc.Keyboard('*.', getLS(30042))
            keybd.doModal()
            if keybd.isConfirmed():
                selected.append(keybd.getText())
                if selected != '*.':
                    mytools.Exceptions(self.current_tab).add_exceptions(selected)
        self.load_list(self.current_tab)

    def disable_enable(self):
        """Enable or disable selected items.
        """
        selected = []
        for i in range(0, self.list.size()):
            if self.list.getListItem(i).getProperty('Checked') == 'True':
                selected.append(self.list.getListItem(i).getProperty('File'))
        if len(selected) == 0:
            xbmcgui.Dialog().ok(getLS(30050), getLS(30051))
        else:
            mytools.log("Entries Sent: %s" %("|".join(selected)))
            mytools.Exceptions(self.current_tab).disable_exceptions(selected)
            self.load_list(self.current_tab)

    def remove_entries(self):
        """Remove selected entries from file.
        """
        selected = []
        for i in range(0, self.list.size()):
            if self.list.getListItem(i).getProperty('Checked') == 'True':
                selected.append(self.list.getListItem(i).getProperty('File'))
        if len(selected) == 0:
            xbmcgui.Dialog().ok(getLS(30050), getLS(30051))
        else:
            mytools.Exceptions(self.current_tab).remove_exceptions(selected)
            self.load_list(self.current_tab)

    def show_downloading(self):
        """Go to downloading view.
        """
        window = GuiMLdonkey(title=getLS(30080))
        window.doModal()
        # Destroy the instance explicitly because
        # underlying xbmcgui classes are not garbage-collected on exit.
        del window
        self.close()

    def show_downloaded(self):
        """Go to downloaded (main) view.
        """
        window = GUI(title=getLS(30000))
        window.doModal()
        # Destroy the instance explicitly because
        # underlying xbmcgui classes are not garbage-collected on exit.
        del window
        self.close()


class GUILibrary(pyxbmct.AddonDialogWindow):
    """Show Library window
    Expects:
        title (str): (optional) Title of the window. Defaults to ''
        files (string array): files to be moved,copied, linked... to library.
    Usage:
        window = GUILibrary(title=getLS(30080),files)
        window.doModal()
        del window
    """

    def __init__(self, title='', files=None, parent=pyxbmct.AddonDialogWindow):
        super(GUILibrary, self).__init__(getLS(30070))
        self.ficheros = files
        self.parent = parent
        self.setGeometry(1180, 620, 15, 4)
        self.define_controls()
        self.place_controls()
        self.actions()
        self.load_list()
        self.set_navigation()
        # Connect a key action (Backspace) to close the window.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close_dialog)
        self.connect(pyxbmct.ACTION_PREVIOUS_MENU, self.close_dialog)

    def define_controls(self):
        """Create controls.
        """
        self.label_source = pyxbmct.Label(getLS(30013))
        self.label_folder = pyxbmct.Label(getLS(30015))
        self.label_destination = pyxbmct.Label(getLS(30014))
        self.list_source = pyxbmct.List(_imageWidth=30, _imageHeight=30, _itemTextXOffset=0)
        self.list_folder = pyxbmct.List(_itemTextXOffset=0)
        self.list_destination = pyxbmct.List(_itemTextXOffset=0)
        self.cancel_button = pyxbmct.Button(getLS(30008))
        self.ok_button = pyxbmct.Button(getLS(30007))

    def place_controls(self):
        """Place controls in window.
        """
        self.placeControl(self.label_source, 0, 0, 1, 2)
        self.placeControl(self.label_folder, 0, 2)
        self.placeControl(self.label_destination, 0, 3)
        self.placeControl(self.list_source, 1, 0, 13, 2)
        self.placeControl(self.list_folder, 1, 2, 13, 1)
        self.placeControl(self.list_destination, 1, 3, 13, 1)
        self.placeControl(self.cancel_button, 14, 3)
        self.placeControl(self.ok_button, 14, 0)

    def actions(self):
        """Link active controls with actions.
        """
        self.connect(self.cancel_button, self.close_dialog)
        self.connect(self.ok_button, self.do_action)
        self.connect(self.list_source, self.change_mode)
        self.connect(self.list_folder, self.select_folder)
        self.connect(self.list_destination, self.change_destination_name)

    def load_list(self):
        """Shows files and indicates proposals for type, destination and filename.
        """
        self.list_source.reset()
        self.list_folder.reset()
        self.list_destination.reset()
        for fichero in self.ficheros:
            self.list_source.addItem(
                mytools.shorten_file(__sourceSize__, fichero))
            self.list_source.getListItem(
                self.list_source.size()-1).setProperty("FileName", fichero)
            analitics = mytools.AnalyzeThis(fichero)
            self.list_source.getListItem(self.list_source.size(
            )-1).setArt({'icon': os.path.join(_media_icon_, analitics.icon)})
            self.list_source.getListItem(
                self.list_source.size()-1).setProperty('Icon', analitics.icon)
            self.list_folder.addItem(mytools.shorten_file(
                __folderSize__, analitics.folder))
            self.list_folder.getListItem(self.list_source.size(
            )-1).setProperty('Folder', analitics.folder)
            self.list_folder.getListItem(self.list_source.size(
            )-1).setProperty('Serie', analitics.titulo_serie)
            self.list_destination.addItem(mytools.shorten_file(
                __folderSize__, analitics.fichero))
            self.list_destination.getListItem(
                self.list_destination.size()-1).setProperty('FileName', analitics.fichero)
            self.list_destination.getListItem(
                self.list_destination.size()-1).setProperty('Analytics_FileName', analitics.fichero)

    def set_navigation(self):
        """Set navigation between controls.
        """
        self.list_source.controlUp(self.ok_button)
        self.list_folder.controlUp(self.ok_button)
        self.list_destination.controlUp(self.ok_button)
        self.list_source.controlDown(self.ok_button)
        self.list_folder.controlDown(self.ok_button)
        self.list_destination.controlDown(self.ok_button)
        self.list_source.controlLeft(self.list_destination)
        self.list_source.controlRight(self.list_folder)
        self.list_folder.controlLeft(self.list_source)
        self.list_folder.controlRight(self.list_destination)
        self.list_destination.controlLeft(self.list_folder)
        self.list_destination.controlRight(self.list_source)
        self.ok_button.setNavigation(self.list_source, self.list_source, self.cancel_button, self.cancel_button)
        self.cancel_button.setNavigation(self.list_destination, self.list_destination, self.ok_button, self.ok_button)
        self.setFocus(self.list_source)

    def select_the_other_lists(self, source_list):
        """Changing focus in one list moves focus in the other two lists.

        Args:
            listControl (pyxbmct.List): current browsing list.
        """
        position = source_list.getSelectedPosition()
        lists = [self.list_source, self.list_folder, self.list_destination]
        i = lists.index(source_list)
        lists[(i+1) % 3].selectItem(position)
        lists[(i+2) % 3].selectItem(position)

    def change_mode(self):
        """Changes mode of list item between tv, block and film.
        """
        #TODO Add do nothing option, apply intelligent name when selecting TV or Movie (possibly 2 options)
        #Possibly extend AnalyzeThis class...
        position = self.list_source.getSelectedPosition()
        icons = ['block.png', 'tv.png', 'film.png']

        current_icon = self.list_source.getSelectedItem().getProperty('Icon')
        i = icons.index(current_icon)
        i = (i+1) % 3
        self.list_source.getSelectedItem().setArt(
            {'icon': os.path.join(_media_icon_, icons[i])})
        self.list_source.getSelectedItem().setProperty('Icon', icons[i])
        if i == 0:
            # Block Option
            self.list_folder.getListItem(position).setLabel("")
            self.list_folder.getListItem(position).setProperty('Folder', "")
            self.list_destination.getListItem(position).setLabel("")
            self.list_destination.getListItem(position).setProperty('FileName', "")
        elif i == 1:
            # TV Series
            self.list_folder.getListItem(position).setProperty('Folder', __addon__.getSetting("tv_library"))
            self.list_folder.getListItem(position).setLabel(mytools.shorten_file(__folderSize__, __addon__.getSetting("tv_library")))
            label = self.list_destination.getListItem(position).getProperty('Analytics_FileName')
            if len(label) < 1:
                label = self.list_source.getSelectedItem().getProperty('FileName')
            if "://" in label:
                separator = '/'
            else:
                separator = os.sep
            label = label.rpartition(separator)
            label = label[2]
            self.list_destination.getListItem(position).setProperty('FileName', label)
            self.list_destination.getListItem(position).setLabel(mytools.shorten_file(__destinationSize__, label))
        elif i == 2:
            # Movies
            self.list_folder.getListItem(position).setProperty('Folder', __addon__.getSetting("video_library"))
            self.list_folder.getListItem(position).setLabel(mytools.shorten_file(__folderSize__, __addon__.getSetting("video_library")))
            label = self.list_destination.getListItem(position).getProperty('Analytics_FileName')
            if len(label) < 1:
                label = self.list_source.getSelectedItem().getProperty('FileName')
            if "://" in label:
                separator = '/'
            else:
                separator = os.sep
            label = label.rpartition(separator)
            label = label[2]
            self.list_destination.getListItem(position).setProperty('FileName', label)
            self.list_destination.getListItem(position).setLabel(mytools.shorten_file(__destinationSize__, label))

    def select_folder(self):
        """Triggers actions when selecting a folder.
        """
        new_folder = xbmcgui.Dialog().yesno(getLS(30015), getLS(30016), getLS(30017))
        position = self.list_folder.getSelectedPosition()
        if new_folder:
            current_dir = self.list_folder.getSelectedItem().getProperty('Folder')
            if "://" in current_dir:
                separator = '/'
            else:
                separator = os.sep
            default_series = self.list_folder.getListItem(position).getProperty('Serie')
            if len(default_series) == 0:
                default_series = self.list_source.getListItem(position).getProperty('FileName').split(separator)
                default_series = default_series[len(default_series)-1]
            kbd = xbmcgui.Dialog().input(getLS(30018), default_series, type=xbmcgui.INPUT_ALPHANUM)
            if kbd != "":
                create_dir = xbmcgui.Dialog().yesno(getLS(30015), getLS(30019), current_dir+kbd)
                if create_dir:
                    resp = xbmcvfs.mkdir(current_dir+kbd)
                    if resp:
                        if "://" in current_dir:
                            separator = '/'
                        else:
                            separator = os.sep
                        self.list_folder.getSelectedItem().setProperty('Folder', current_dir+kbd+separator)
                        self.list_folder.getSelectedItem().setLabel(mytools.shorten_file(__folderSize__, current_dir+kbd+separator))
                    else:
                        xbmcgui.Dialog().ok(getLS(30050), getLS(30052), getLS(30053)+kbd)
        else:
            selected = xbmcgui.Dialog().browse(0, getLS(30040), 'files', '', False, False, self.list_folder.getSelectedItem().getProperty('Folder'))
            if selected is not self.list_folder.getSelectedItem().getProperty('Folder'):
                self.list_folder.getSelectedItem().setProperty('Folder', selected)
                self.list_folder.getSelectedItem().setLabel(mytools.shorten_file(__folderSize__,
                                                                                 selected))
        if self.list_source.getListItem(position).getProperty('Icon') == 'tv.png' and self.list_folder.getSelectedItem().getProperty('Folder') != __addon__.getSetting("tv_library"):
            serie_actual = self.list_folder.getSelectedItem().getProperty('Folder')
            if serie_actual.endswith("/") or serie_actual.endswith("\\"):
                serie_actual = serie_actual[:-1]
            if "://" in serie_actual:
                separator = '/'
            else:
                separator = os.sep
            serie_actual = serie_actual.rpartition(separator)
            serie_actual = serie_actual[2]
            new_series_assignment = self.list_folder.getListItem(position).getProperty('Serie')+" --> "+serie_actual
            if xbmcgui.Dialog().yesno(getLS(30055), getLS(30056), new_series_assignment):
                mytools.add_series_assignment(new_series_assignment)
                if xbmcgui.Dialog().yesno(getLS(30055), getLS(30057), ""):
                    for item_id in range(self.list_source.size()):
                        if self.list_source.getListItem(item_id).getProperty('Icon') == 'block.png':
                            analitics = mytools.AnalyzeThis(self.list_source.getListItem(item_id).getProperty('FileName'))
                            self.list_source.getListItem(item_id).setArt(
                                {'icon': os.path.join(_media_icon_, analitics.icon)})
                            self.list_source.getListItem(item_id).setProperty(
                                'Icon', analitics.icon)
                            self.list_folder.getListItem(item_id).setProperty(
                                'Folder', analitics.folder)
                            self.list_folder.getListItem(item_id).setLabel(
                                mytools.shorten_file(__folderSize__, analitics.folder))
                            self.list_folder.getListItem(item_id).setProperty(
                                'Serie', analitics.titulo_serie)
                            self.list_destination.getListItem(item_id).setProperty(
                                'FileName', analitics.fichero)
                            self.list_destination.getListItem(item_id).setLabel(
                                mytools.shorten_file(__destinationSize__, analitics.fichero))

    def change_destination_name(self):
        """Change destination Name
        """
        kbd = xbmcgui.Dialog().input(getLS(30043), self.list_destination.getSelectedItem(
        ).getProperty('FileName'), type=xbmcgui.INPUT_ALPHANUM)
        if kbd is not "":
            self.list_destination.getSelectedItem().setLabel(kbd)
            self.list_destination.getSelectedItem().setProperty('FileName', kbd)

    def do_action(self):
        """Perform selected action on files.
        """
        operation = {"0" : "copy", "1" : "move", "2" : "hard link", "3" : "symlink", "4" : "test"}
        operation = operation[__addon__.getSetting('tipo')]
        p_dialog = xbmcgui.DialogProgress()

        header = 30045+int(__addon__.getSetting('tipo'))
        p_dialog.create(getLS(header), getLS(30049))

        for i in range(0, self.list_source.size()):
            p_dialog.update(100*i/self.list_source.size())
            if not self.list_source.getListItem(i).getProperty('Icon') == 'block.png':
                source = self.list_source.getListItem(i).getProperty('FileName')
                destination = self.list_folder.getListItem(i).getProperty('Folder')+self.list_destination.getListItem(i).getProperty('FileName')
                # result = work_in_files.LibraryOperations(operation, source, destination).result
                result = mytools.library_operations(operation, source, destination)
                if not result:
                    xbmcgui.Dialog().ok(getLS(30050), getLS(30052), operation+" "+source, "--> "+destination)
                    break
            else:
                source = self.list_source.getListItem(i).getProperty('FileName')
                # work_in_files.addExceptions('file', source)
                mytools.Exceptions().add_exceptions(source)
        self.close_dialog()


    def close_dialog(self):
        """Close Dialog.
        """
        self.parent.load_list()
        self.close()

class GUIPattern(pyxbmct.AddonDialogWindow):
    """Filter Window - Shows files, directories and extensions.

    Child of pyxbmct.AddonDialogWindow
    TODO define better inheritance - should be son of GUI
    Args:
        title (str, optional): Header of window. Defaults to ''.

    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, title=''):
        """GUI_Filter constructor

        Args:
            title (str, optional): Defaults to ''.
        """
        super(GUIPattern, self).__init__(title)
        self.pattern_types = {
            "tv_detect": "[TV Episode detection]",
            "tv_extract": "[TV Episode series extract]",
            "clean": "[Clean]"
        }
        self.setGeometry(1180, 620, 16, 7)
        self.define_controls()
        self.place_controls()
        self.actions()
        self.load_list()
        self.set_navigation()
        # Connect a key action (Backspace) to close the window.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
        self.current_tab = 'tv_detect'


    def define_controls(self):
        """Defines controls.
        """
        self.tab_downloaded = pyxbmct.Button(getLS(30001))
        self.downloading_tab = pyxbmct.Button(getLS(30003))
        self.exceptions_tab = pyxbmct.Button(getLS(30002))
        self.is_tv_button = pyxbmct.Button(getLS(30063))
        self.tv_extract_button = pyxbmct.Button(getLS(30064))
        self.clean_button = pyxbmct.Button(getLS(30065))
        self.keyboard_button = pyxbmct.Button(getLS(30066))
        self.disable_button = pyxbmct.Button(getLS(30034))
        self.edit_button = pyxbmct.Button(getLS(30022))
        self.remove_button = pyxbmct.Button(getLS(30035))
        self.info = pyxbmct.Label(getLS(30066))
        self.list = pyxbmct.List(_imageWidth=20, _imageHeight=20, _itemTextXOffset=0)
        self.back_button = pyxbmct.Button(getLS(30009))

    def place_controls(self):
        """Place controls.
        """
        self.placeControl(self.tab_downloaded, 0, 0, 1, 2)
        self.placeControl(self.downloading_tab, 0, 2, 1, 2)
        self.placeControl(self.exceptions_tab, 0, 4, 1, 2)
        self.placeControl(self.info, 1, 0, 1, 7)
        self.placeControl(self.is_tv_button, 2, 0, 1, 2)
        self.placeControl(self.tv_extract_button, 2, 2, 1, 2)
        self.placeControl(self.clean_button, 2, 4, 1, 2)
        self.placeControl(self.list, 3, 0, 13, 6)
        self.placeControl(self.back_button, 15, 0, 1, 6)
        self.placeControl(self.keyboard_button, 3, 6, 2, 1)
        self.placeControl(self.edit_button, 6, 6, 2, 1)
        # self.placeControl(self.disable_button, 6, 6, 2, 1)
        self.placeControl(self.remove_button, 9, 6, 2, 1)

    def set_navigation(self):
        """Define how button navigation is done.
        """
        self.tab_downloaded.setNavigation(self.back_button, self.is_tv_button, self.exceptions_tab, self.downloading_tab)
        self.downloading_tab.setNavigation(self.back_button, self.is_tv_button, self.tab_downloaded, self.exceptions_tab)
        self.exceptions_tab.setNavigation(self.back_button, self.is_tv_button, self.downloading_tab, self.tab_downloaded)
        self.back_button.controlUp(self.list)
        self.back_button.controlDown(self.tab_downloaded)
        self.list.setNavigation(self.is_tv_button, self.back_button, self.keyboard_button, self.keyboard_button)
        self.is_tv_button.setNavigation(self.tab_downloaded, self.list, self.clean_button, self.tv_extract_button)
        self.tv_extract_button.setNavigation(self.tab_downloaded, self.list, self.is_tv_button, self.clean_button)
        self.clean_button.setNavigation(self.tab_downloaded, self.list, self.tv_extract_button, self.is_tv_button)
        self.keyboard_button.setNavigation(self.remove_button, self.edit_button, self.list, self.list)
        self.edit_button.setNavigation(self.keyboard_button, self.remove_button, self.list, self.list)
        self.remove_button.setNavigation(self.edit_button, self.keyboard_button, self.list, self.list)
        # self.keyboard_button.setNavigation(self.remove_button, self.disable_button, self.list, self.list)
        # self.disable_button.setNavigation(self.keyboard_button, self.remove_button, self.list, self.list)
        # self.remove_button.setNavigation(self.disable_button, self.keyboard_button, self.list, self.list)
        # Set initial focus
        self.setFocus(self.is_tv_button)

    def actions(self):
        """Connect controls with actions.
        """
        self.connect(self.back_button, self.show_downloaded)
        self.connect(self.exceptions_tab, self.manage_exceptions)
        self.connect(self.downloading_tab, self.show_downloading)
        self.connect(self.tab_downloaded, self.show_downloaded)
        self.connect(self.tv_extract_button, lambda: self.load_list('tv_extract'))
        self.connect(self.clean_button, lambda: self.load_list('clean'))
        self.connect(self.is_tv_button, lambda: self.load_list('tv_detect'))
        self.connect(self.keyboard_button, self.add_pattern)
        self.connect(self.disable_button, self.disable_enable)
        self.connect(self.edit_button, self.edit_pattern)
        self.connect(self.remove_button, self.remove_entries)
        self.connect(self.list, self.check_uncheck)

    def load_list(self, exception_type='tv_detect'):
        """Reloads list from current tab.

        Args:
            exception_type (str, optional): File that indicates current tab [tv_detect|tv_extract|clean]. Defaults to 'tv_extract'.
        """

        # web_pdb.set_trace()
        patterns = mytools.Patterns(self.pattern_types[exception_type]).search_pattern()
        patterns = patterns.split("|")
        self.list.reset()
        for item in patterns:
            self.list.addItem(item)
            self.list.getListItem(self.list.size()-1).setProperty('File', item)
            # if item.startswith("!"):
            #     self.list.getListItem(self.list.size()-1).setLabel("[COLOR grey][I]" + item + "[/I][/COLOR]")
            if item == "_Nothing":
                self.list.getListItem(self.list.size()-1).setLabel("")
        self.current_tab = exception_type
        type_label = {'tv_detect': 30067, 'tv_extract': 30068, 'clean': 30069}
        self.info.setLabel(getLS(type_label[exception_type]))
        if self.list.size() == 0:
            self.list.addItem("")

    def check_uncheck(self):
        """Check or uncheck list items.
        """
        list_item = self.list.getSelectedItem()
        if list_item.getProperty('Checked') == "True":
            list_item.setArt({'icon': ""})
            list_item.setProperty('Checked', "False")
        else:
            list_item.setArt({'icon': _check_icon_})
            list_item.setProperty('Checked', "True")

    def add_pattern(self):
        """Open Keyboard dialog to add a new pattern.
        """
        keybd = xbmc.Keyboard('', getLS(30071))
        keybd.doModal()
        if keybd.isConfirmed():
            selected = keybd.getText()
            if selected != '':
                mytools.Patterns(self.pattern_types[self.current_tab]).add_pattern(selected)
        self.load_list(self.current_tab)

    def edit_pattern(self):
        """Open Keyboard dialog to edit a new pattern.
        """
        selected = []
        for i in range(0, self.list.size()):
            if self.list.getListItem(i).getProperty('Checked') == 'True':
                selected.append(self.list.getListItem(i).getProperty('File'))
        if len(selected) == 0:
            xbmcgui.Dialog().ok(getLS(30050), getLS(30054))
        else:
            if len(selected) > 1:
                xbmcgui.Dialog().ok(getLS(30055), getLS(30058))
            keybd = xbmc.Keyboard(selected[0], getLS(30071))
            keybd.doModal()
            if keybd.isConfirmed():
                edited_entry = keybd.getText()
                if edited_entry != '' and edited_entry != selected[0]:
                    mytools.Patterns(self.pattern_types[self.current_tab]).edit_pattern(edited_entry, selected[0])
        self.load_list(self.current_tab)

    def disable_enable(self):
        """Enable or disable selected items.
        """
        selected = []
        for i in range(0, self.list.size()):
            if self.list.getListItem(i).getProperty('Checked') == 'True':
                selected.append(self.list.getListItem(i).getProperty('File'))
        if len(selected) == 0:
            xbmcgui.Dialog().ok(getLS(30050), getLS(30051))
        else:
            mytools.log("Entries Sent: %s" %("|".join(selected)))
            mytools.Exceptions(self.current_tab).disable_exceptions(selected)
            self.load_list(self.current_tab)

    def remove_entries(self):
        """Remove selected entries from file.
        """
        selected = []
        for i in range(0, self.list.size()):
            if self.list.getListItem(i).getProperty('Checked') == 'True':
                selected.append(self.list.getListItem(i).getProperty('File'))
        if len(selected) == 0:
            xbmcgui.Dialog().ok(getLS(30050), getLS(30054))
        else:
            mytools.Patterns(self.pattern_types[self.current_tab]).remove_patterns(selected)
            self.load_list(self.current_tab)

    def show_downloading(self):
        """Go to downloading view.
        """
        window = GuiMLdonkey(title=getLS(30080))
        window.doModal()
        # Destroy the instance explicitly because
        # underlying xbmcgui classes are not garbage-collected on exit.
        del window
        self.close()

    def show_downloaded(self):
        """Go to downloaded (main) view.
        """
        window = GUI(title=getLS(30000))
        window.doModal()
        # Destroy the instance explicitly because
        # underlying xbmcgui classes are not garbage-collected on exit.
        del window
        self.close()

    def manage_exceptions(self):
        """Go to Exceptions window.
        """
        window = GUIFilter(title=getLS(30029))
        window.doModal()
        # Destroy the instance explicitly because
        # underlying xbmcgui classes are not garbage-collected on exit.
        del window
        self.close()
