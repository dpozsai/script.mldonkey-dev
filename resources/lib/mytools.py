# coding=utf-8
"""Common place to locate functions and helper classes.
"""

from __future__ import unicode_literals

import io
import os
import sys
import configparser
import re
import fnmatch
# import fileinput
import xbmc
import xbmcgui
# import xbmcplugin
import xbmcvfs

###Debug
import web_pdb
#web_pdb.set_trace()


__addon__ = sys.modules["__main__"].__addon__
__addondir__ = xbmcvfs.translatePath(__addon__.getAddonInfo('profile'))
__cwd__ = sys.modules["__main__"].__cwd__
__subtitles__ = ['.srt']


if __addondir__.endswith("/") or __addondir__.endswith("\\"):
    __separator__ = ''
elif "://" in __addondir__:
    __separator__ = '/'
else:
    __separator__ = os.sep

__excludedExtensions__ = __addondir__ + __separator__ + "excludedExtensions.txt"
__excludedFiles__ = __addondir__ + __separator__ + "excludedFiles.txt"
__excludedDirectories__ = __addondir__ + \
    __separator__ + "excludedDirectories.txt"
__patterns__ = __addondir__ + __separator__ + "patterns.txt"
__patterns2__ = __addondir__ + __separator__ + "patterns2.txt"
__sudoer__ = False

getLS = sys.modules["__main__"].__language__


def log(txt, level=xbmc.LOGDEBUG):
    """Log string to Kodi with DEBUG level

    Args:
        txt (str): String that will be sent to log
        level ([int], optional): Log LEVEL. Defaults to xbmc.LOGDEBUG.
    """
    # txt = txt.decode("utf-8")
    # xbmc.log(msg=txt.encode('utf-8'), level=level)
    xbmc.log(msg=txt, level=level)

def open_or_new(fichero, operation='r'):
    """Opens exception file, creates a new file is missing.

    Args:
        fichero (file descriptor): file to be used
        operation (string): defaults to "r", also valid "w"

    Usage:
        f_extensiones = open_or_new("file",r)

    Returns:
        file descriptor: the file used or the new one.
    """
    if operation in ('r', 'w', 'r+', 'w+', 'a'):
        try:
            file = io.open(fichero, operation, encoding='utf-8')
        except IOError:
            file = open(fichero, 'w+')
            file.write(
                "#Extensions, files or directories to be excluded from listing.\n")
            file.write(
                "#One line per entry, extensions beginning by a asterisk dot (*.), relative paths for files and directories\n")
            file.flush()
        return file
    raise "Wrong option"


def list_files():
    """Function that list downloaded files.

    Usage: mytools.LoadList()

    Example: file_list = mytools.list_files()

    Returns:
        [type]: [description]
    """

    # # def open_or_new(fichero):
    #     """Opens exception file, creates a new file is missing.

    #     Args:
    #         fichero (file descriptor): file to be used

    #     Returns:
    #         file descriptor: the file used or the new one.
    #     """
    #     try:
    #         file = open(fichero, 'r')
    #     except IOError:
    #         file = open(fichero, 'w+')
    #         file.write(
    #             "#Extensions, files or directories to be excluded from listing.\n")
    #         file.write(
    #             "#One line per entry, extensions beginning by a asterisk dot (*.), relative paths for files and directories\n")
    #         file.flush()
    #     return file

    def loop_and_quit_comments(file_desc):
        """Return clean file without comments.

        Version bypassing lines starting with # and !

        Args:
            file_desc (file descriptor): File analysed

        Returns:
            str[]: all lines of the file
        """
        entries = []
        for line in file_desc:
            if not (line.startswith('#') or line.startswith('!')):
                entries.append(line.strip())
        file_desc.close()
        return entries

    # log("[SCRIPT] ListFiles called")
    base = __addon__.getSetting("folder")

    f_extensiones = open_or_new(__excludedExtensions__, 'r')
    f_files = open_or_new(__excludedFiles__, 'r')
    f_directories = open_or_new(__excludedDirectories__, 'r')

    if xbmcvfs.exists(base):
        progress_dialog = xbmcgui.DialogProgress()
        progress_dialog.create(getLS(30025), getLS(30026))
        ficheros = []
        exclude_extensions = loop_and_quit_comments(f_extensiones)
        exclude_directories = loop_and_quit_comments(f_directories)
        exclude_files = loop_and_quit_comments(f_files)
        exclude_files = exclude_extensions + exclude_files

        exclude_directories = r'|'.join(
            [fnmatch.translate(x) for x in exclude_directories]) or r'$.'
        exclude_directories = exclude_directories.replace('[', '\\[')
        exclude_directories = exclude_directories.replace(']', '\\]')
        exclude_files = r'|'.join([fnmatch.translate(x)
                                   for x in exclude_files]) or r'$.'
        exclude_files = exclude_files.replace('[', '\\[')
        exclude_files = exclude_files.replace(']', '\\]')

        subdirs, files = xbmcvfs.listdir(base)
        root = base
        progress_dialog.update(1)
        if root.endswith("/") or root.endswith("\\"):
            separator = ''
        elif "://" in root:
            separator = '/'
        else:
            separator = os.sep
        files = [(root + separator + f) for f in files]
        subdirs = [(root + separator + d) for d in subdirs]

        # log("[SCRIPT] Files %s" % ("|".join(files)))
        # log("[SCRIPT] Directories %s" % ("|".join(subdirs)))
        leido = 0
        while len(subdirs) > 0:
            next_dir = subdirs.pop()
            leido = leido+1
            progress_dialog.update(
                int(100*leido/(leido+len(subdirs))), getLS(30026) + " " + next_dir)
            if progress_dialog.iscanceled():
                break
            if not re.match(exclude_directories, next_dir):
                try:
                    newdirs, newfiles = xbmcvfs.listdir(next_dir)
                    if next_dir.endswith("/") or root.endswith("\\"):
                        separator = ''
                    elif "://" in next_dir:
                        separator = '/'
                    else:
                        separator = os.sep
                    newdirs = [(next_dir + separator + d) for d in newdirs]
                    subdirs = subdirs + newdirs
                    newfiles = [(next_dir + separator + f) for f in newfiles]
                    files = files + newfiles
                # except (NotADirectoryError, PermissionError, TimeoutError, FileNotFoundError):
                # FUTURE replace in Python 3
                except IOError:
                    log("Error reading %s" % (next_dir))
                    break

        files = [f for f in files if not re.match(exclude_files, f)]
        # log("[SCRIPT] Files not matching %s" % ("|".join(files)))
        # log("[SCRIPT] Files not matching %s" % (exclude_files))
        progress_dialog.update(100)
        progress_dialog.update(0, getLS(30027))
        verificar = False
        if __addon__.getSetting('tipo') in ["2", "3"] and __addon__.getSetting('link_filter').lower() == "true":
            # id="tipo" type="enum" lvalues="copy|move|hardlink|symlink"
            # id="link_filter" type="bool"
            # If file is linked, and filter option is set to true (default), do not show files that are linked in destination folder
            verificar = True
        for fname in files:
            leido += 1
            progress_dialog.update(int(100*leido/len(files)), getLS(30027) + " " + fname)
            if verificar:
                stat = xbmcvfs.Stat(fname)
                if stat.st_nlink() < 2:
                    ficheros.append(fname)
            #        print "XXXXXX" + fname + " links:"+str(stat.st_nlink())
            #    print fname + " links:"+str(stat.st_nlink())
            else:
                ficheros.append(fname)
            if progress_dialog.iscanceled():
                break
        #    print fname
        #    print "st_atime" + str(stat.st_atime())
        #    print "st_ctime" + str(stat.st_ctime())
        #    print "st_dev" + str(stat.st_dev())
        #    print "st_gid" + str(stat.st_gid())
        #    print "st_ino" + str(stat.st_ino())
        #    print "st_mode" + str(stat.st_mode())
        #    print "st_mtime" + str(stat.st_mtime())
        #    print "st_nlink" + str(stat.st_nlink())
        #    print "st_size" + str(stat.st_size())
        #    print "st_uid" + str(stat.st_uid())
        progress_dialog.close()
    #    if len(ficheros)==0:
    #        ficheros=['---Empty---']
        ficheros.sort()

    else:
        ficheros = ["Error in root folder definition"]

    return ficheros


def shorten_file(size, string):
    """Returns a shorter version of a full path.

    Keeps beginning and end.

    Example:
        string = mytools.shorten_file(100, "/home/file.txt")

    Args:
        size (int): max size of the final str
        string (string): path of file

    Returns:
        string: shorter version of the file path
    """

    __initial_size__ = 1
    if size >= len(string):
        return string
    if "://" in string:
        separator = '/'
    else:
        separator = os.sep
    string_parts = string.split(separator)
    contador = 0
    mylen = 0
    while not (len(string) <= size or len(string_parts) == 1):
        mylen = mylen + len(string_parts.pop(0))
        if mylen > __initial_size__:
            string = string[:contador] + \
                separator + string[mylen+contador+1:]
            contador += __initial_size__
            mylen = 0
    return string

def add_series_assignment(assignment):
    """Creates a relation between a file beginngin and a TV Series for later use.

    Args:
        assignment (str): The intitial part of the file name, "-->" and the TV series
    """

    def mi_open_rw():
        """Open or create new file for series assignment.

        Returns:
            fdesc: File descriptor of the file
        """
        if os.path.isfile(__patterns2__):
            fdesc = open(__patterns2__, 'w+')
        else:
            fdesc = open(__patterns2__, 'w+')
            fdesc.write("#Patterns to look for.\n")
            fdesc.write("#Sections separated by [ ]\n")
            fdesc.write("[TV Episode series assign]\n")
            fdesc.flush()
        return fdesc

    assignment = assignment.split("-->")
    parser = configparser.ConfigParser()
    parser.read(__patterns2__)
    if parser.has_section('TV Episode series assign'):
        parser.set('TV Episode series assign',
                   assignment[0], assignment[1])
        fpatterns = mi_open_rw()
        parser.write(fpatterns)


def library_operations(operation, source, destination):
    """Performs file actions on an item

    Args:
        operation (str): {"copy", "move", "hard link", "symlink", "test"}
        source (str): source path
        destination (str): destination path

    Returns:
        bool: True if OK, False if NOK.
    """
    result = False

    if operation == 'copy':
        result = xbmcvfs.copy(source, destination)
        if result:
            # addExceptions('file', source)
            Exceptions().add_exceptions([source])

    elif operation == 'move':
        result = xbmcvfs.copy(source, destination)
        if result:
            result = xbmcvfs.delete(source)

    elif operation == 'hard link':
        try:
            os.link(source, destination)
            result = True
            if not __addon__.getSetting('link_filter'):
                # addExceptions('file', source)
                Exceptions().add_exceptions([source])
        except OSError as event:
            result = False
            log("Error with hard link operation", xbmc.LOGERROR)
            log(event.strerror, xbmc.LOGERROR)
            log("SOURCE:"+source, xbmc.LOGERROR)
            log("DESTINATION"+destination, xbmc.LOGERROR)

    elif operation == 'symlink':
        try:
            os.symlink(source, destination)
            Exceptions().add_exceptions([source])
            result = True
        except OSError as event:
            result = False
            log("Error with symlink operation", xbmc.LOGERROR)
            log(event.strerror, xbmc.LOGERROR)
            log("SOURCE:"+source, xbmc.LOGERROR)
            log("DESTINATION"+destination, xbmc.LOGERROR)

    elif operation == 'test':
        xbmcgui.Dialog().notification("Test operations", operation + " : " + source +
                                      "-->" + destination, xbmcgui.NOTIFICATION_WARNING, 3000)
        Exceptions().add_exceptions([source])
        result = True

    return result


class Exceptions:
    """Exception class.
    Provides support for exception operations.
    """
    def __init__(self, tipo="file"):
        """Constructor

        Args:
            tipo (str, optional): Type of exception file. Defaults to "file".
                Only file|directory|extension

        Raises:
            Exception: If tipo is not one of file|directory|extension
        """
        self.file = ""
        # log("Exceptions - called")
        if tipo == 'directory':
            self.file = __excludedDirectories__
        elif tipo == 'file':
            self.file = __excludedFiles__
        elif tipo == 'extension':
            self.file = __excludedExtensions__
        else:
            raise Exception

    def loop_and_quit_comments(self, fdesc):
        """Read file and return uncommented lines.

        return lines that do not start with #

        Args:
            fdesc (File descriptor): File to return

        Returns:
            [ string array ]: List of lines of file.
        """
        entries = []
        for line in fdesc:
            # log("Reading exception file: %s" %(line))
            if not line.startswith('#'):
                entries.append(line.strip())
        return entries

    def list_exceptions(self):
        """List lines in exception file.

        Returns:
            [ str ]: List of lines in file.
        """
        fexception = open_or_new(self.file, 'r')
        exceptions = self.loop_and_quit_comments(fexception)
        # log("Resultado: %s" %("\n".join(exceptions)))
        fexception.close()
        return exceptions

    def add_exceptions(self, list_entries):
        """Add selected files or directories to extension file.

        Args:
            list_entries ([ str ]): List of lines to be added
        """
        try:
            iter(list_entries)
        except TypeError:
            list_entries = [list_entries]
        else:
            list_entries = list(list_entries)

        fexception = open_or_new(self.file, 'a')
        # log('File contents: %s' % ("|".join(contents)))
        for exception in list_entries:
            if exception.endswith("/") or exception.endswith("\\"):
                exception = exception[:-1]
            fexception.write(exception+"\n")
        fexception.close()

    def disable_exceptions(self, list_entries):
        """Disable the given list of entries in exceptions file.

        Args:
            list_entries ([ str ]): List of lines of file
        """
        # log("Disable Exceptions - called")
        # log("Entries: %s" %("|".join(list_entries)))

        search_expr = r'|'.join([fnmatch.translate(x)
                                 for x in list_entries]) or r'$.'
        search_expr = search_expr.replace('[', '\\[')
        search_expr = search_expr.replace(']', '\\]')
        fexception = open_or_new(self.file, 'r')
        file_content = fexception.readlines()
        fexception.close()
        # log("File size pre - %i" %(len(file_content)))
        # log("File content pre: %s" % ("*".join(file_content)))

        for num, line in enumerate(file_content):
            line = line.strip()
            # log("%i Checking: %s vs. %s" %(num, line, search_expr))
            if re.match(search_expr, line):
                # log("Disable: %s" %(line))
                if line[0] == "!":
                    line = line[1:]
                else:
                    line = "!"+line
                line = line + "\n"
                file_content[num] = line
            # log("Do nothing: %s" % (line))
        fexception = open_or_new(self.file, 'w+')
        # log("File size post - %i" %(len(file_content)))
        # log("File content post: %s" % ("*".join(file_content)))
        fexception.writelines(file_content)
        fexception.close()

    def remove_exceptions(self, list_entries):
        """Remove lines from file.

        Args:
            list_entries ([ str ]): List of lines to be removed.
        """
        search_expr = r'|'.join([fnmatch.translate(x)
                                 for x in list_entries]) or r'$.'
        search_expr = search_expr.replace('[', '\\[')
        search_expr = search_expr.replace(']', '\\]')
        fexception = open_or_new(self.file, 'r')
        file_content = fexception.readlines()
        fexception.close()
        file_content_new = []
        for line in file_content:
            line = line.strip()
            # log("Checking: %s vs. %s" %(line, search_expr))
            if not re.match(search_expr, line):
                # log("Not remove: %s" %(line))
                line = line+"\n"
                file_content_new.append(line)
        fexception = open_or_new(self.file, 'w')
        fexception.writelines(file_content_new)
        fexception.close()

class AnalyzeThis:
    """Defines structure of files to be imported to library

    Expects:
        file_original (str): Original filename.

    Variables:
        fichero (str): clean filename
        icon (str): type icon filename
        folder (str): folder where the file will be located
        titulo_serie (str): name of the TV series

    """
    def __init__(self, file_original):
        # web_pdb.set_trace()
        tv_series = self.get_tv_series()
        if "://" in file_original:
            separator = '/'
        else:
            separator = os.sep
        self.fichero = file_original.rpartition(separator)
        self.fichero = self.fichero[2]
        ending = file_original.rpartition('.')
        ending = (ending[1]+ending[2]).lower()
        pattern_tv = Patterns('[TV Episode detection]').search_pattern()
        if ending in xbmc.getSupportedMedia('video') or ending in __subtitles__:
            if re.search(pattern_tv, self.fichero, re.IGNORECASE):
                pattern_assign = Patterns('[TV Episode series extract]').search_pattern()
                serie = re.findall(pattern_assign, self.fichero, re.IGNORECASE)
            #    serie= filter(None, [e for t in serie for e in t])
                serie = [serie[0][i:i+4]
                         for i in range(0, serie[0].__len__(), 4) if serie[0][i+1]]  # new
                serie = [e for t in serie for e in t]
                self.titulo_serie = self.clean(serie[0])
                if not self.titulo_serie:
                    directorio = file_original.rpartition(separator)
                    directorio = directorio[0]
                    directorio = directorio.rpartition(separator)
                    directorio = directorio[2]
                    self.titulo_serie = self.clean(directorio)
                temporada = int(serie[1])
                episodio = int(serie[2])
                capitulo = serie[3]
                ending = capitulo.rpartition('.')
                ending = (ending[1]+ending[2]).lower()
                capitulo = capitulo[:-len(ending)]
                if ending in __subtitles__:
                    ending2 = capitulo.rpartition('.')
                    ending2 = (ending2[1]+ending2[2]).lower()
                    ending = ending2+ending
                    capitulo = capitulo[:-len(ending2)]
                capitulo = self.clean(capitulo)
                self.icon = "tv.png"
                parser = configparser.ConfigParser()
                parser.read(__patterns2__, encoding='utf-8')
                if self.titulo_serie in tv_series:
                    titulo = __addon__.getSetting(
                        "tv_library")+self.titulo_serie
                elif parser.has_option('TV Episode series assign', self.titulo_serie):
                    titulo = __addon__.getSetting(
                        "tv_library")+parser.get('TV Episode series assign', self.titulo_serie)
                else:
                    titulo = __addon__.getSetting("tv_library")
                    self.icon = "block.png"
                if not titulo.endswith(separator):
                    titulo = titulo+separator
                self.folder = titulo
                if len(capitulo) > 0:
                    self.fichero = '{0:02}x{1:02} {2}{3}'.format(
                        temporada, episodio, capitulo, ending)
                else:
                    self.fichero = '{0:02}x{1:02}{2}'.format(
                        temporada, episodio, ending)

            else:
                self.icon = "film.png"
                self.folder = __addon__.getSetting("video_library")
                self.fichero = self.fichero[:-len(ending)]
                self.fichero = self.clean(self.fichero)+ending
                self.titulo_serie = ""
        else:
            self.icon = "block.png"
            self.folder = ""
            self.fichero = ""
            self.titulo_serie = ""

    def clean(self, fichero):
        """Returns downloaded filename keeping the important information.

        Removes known characters in downloaded files. Changes "." with " "

        Args:
            fichero (string): original filename

        Returns:
            str: filename without known patterns.
        """
        #pylint: disable=anomalous-backslash-in-string
        expr = Patterns('[Clean]').search_pattern()
        fichero = " ".join(
            re.split("[^a-zA-Z0-9ñáéíóúäëïöüÑÁÉÍÓÚÄËÏÖÜ\[\]\(\)€çÇ]+", fichero))
        fichero = re.sub(expr, "", fichero)
        fichero = fichero.strip()
        return fichero

    def get_tv_series(self):
        """Return TV series directories.

        Returns:
            [string array]: List of folders in TV source.
        """
        #pylint: disable=unused-variable, no-self-use
        base = __addon__.getSetting("tv_library")
        dirs, files = xbmcvfs.listdir(base)
        return dirs

class Patterns:
    """Patterns class.
    Provides support for patterns operations.
    """
    def __init__(self, tipo):
        """Constructor

        Args:
            tipo: Section of the patterns file
        Raises:
            Exception: If tipo is not one of "[TV Episode detection]", "[TV Episode series extract]" or "[Clean]"
        """
        self.tipo = tipo

    def open_patterns(self, operation='r'):
        """Opens patterns file or creates a new blank one if missing.

        Args:
            operation (str, optional): File operation in ('r', 'w', 'r+', 'w+', 'a'). Defaults to 'r'.

        Returns:
            filedesc: filedescriptor of the patterns file.
        """

        #pylint: disable=no-self-use

        if operation in ('r', 'w', 'r+', 'w+', 'a'):
            try:
                filedesc = io.open(__patterns__, operation, encoding='utf-8')
            except IOError:
                filedesc = open(__patterns__, 'w+')
                filedesc.write("#Patterns to look for.\n")
                filedesc.write("#Sections separated by [ ]\n")
                filedesc.write("[TV Episode detection]\n")
                filedesc.write("\\d{1,2}[xe]\\d{1,2}\n")
                filedesc.write("(.*)Cap.*(\\d)(\\d{2})(.*)\n")
                filedesc.write("(\\w{2,3})(\\d)(\\d{2})(.*)\n")
                filedesc.write("\n")
                filedesc.write("[TV Episode series extract]\n")
                filedesc.write("(.*)[ts]?(\\d{2})[xe](\\d{1,2})(.*)\n")
                filedesc.write("(.*)[ts]?(\\d{1})[xe](\\d{1,2})(.*)\n")
                filedesc.write("(.*)Cap.*(\\d)(\\d{2})(.*)\n")
                filedesc.write("(\\w{2,3})(\\d)(\\d{2})(.*)\n")
                filedesc.write("\n")
                filedesc.write("[Clean]\n")
                filedesc.flush()
            return filedesc
        raise "Wrong option"


    def search_pattern(self):
        """Returns the patterns of the section in file

        Args:

        Returns:
            [string array]: Patterns of file corresponding to the section.
        """
        fpattern = self.open_patterns()
        go_on = False
        pattern = []
        for line in fpattern.readlines():
            if go_on:
                if line.startswith('['):
                    go_on = False
                elif line.strip() == "":
                    pass
                else:
                    pattern.append(line.strip())
            if line.startswith(self.tipo):
                go_on = True
        if len(pattern) == 0:
            pattern.append("_Nothing")
        pattern = "|".join(pattern)
        fpattern.close()
        return pattern

    def add_pattern(self, reg_text):
        """Adds a new pattern in appropriate section

        Args:
            reg_text ([str]): Pattern to add.
        """
        # web_pdb.set_trace()
        fpattern = self.open_patterns()
        contents = fpattern.readlines()
        fpattern.close()

        go_on = False
        i = 0
        for line in contents:
            if go_on:
                if line.startswith('['):
                    go_on = False
                elif line.strip() == "":
                    contents.insert(i, reg_text + "\n")
                    break
            if line.startswith(self.tipo):
                go_on = True
            i = i+1
        if len(contents) <= i:
            contents.insert(i, reg_text + "\n")

        fpattern = self.open_patterns(operation='w')
        # contents = "".join(contents)
        fpattern.writelines(contents)
        fpattern.flush()
        fpattern.close()

    def remove_patterns(self, list_entries):
        """Removes patterns of appropriate section.

        Args:
            list_entries ([ str ]): List of lines to be removed.
        """
        # web_pdb.set_trace()

        fpattern = self.open_patterns()
        contents = fpattern.readlines()
        fpattern.close()

        go_on = False
        file_content_new = []

        for line in contents:
            line = line.strip()

            if go_on:
                if line.startswith('['):
                    go_on = False
                    line = line+"\n"
                    file_content_new.append(line)
                elif not line in list_entries:
                    line = line+"\n"
                    file_content_new.append(line)
            elif line.startswith(self.tipo):
                go_on = True
                line = line+"\n"
                file_content_new.append(line)
            else:
                line = line+"\n"
                file_content_new.append(line)

        fpattern = self.open_patterns(operation='w')
        fpattern.writelines(file_content_new)
        fpattern.flush()
        fpattern.close()

    def edit_pattern(self, new_entry, old_entry):
        """Edits a patterns of appropiate section.

        Args:
            new_entry (str): new entry
            old_entry (str): replaced entry
        """
        fpattern = self.open_patterns()
        contents = fpattern.readlines()
        fpattern.close()

        go_on = False
        file_content_new = []

        for line in contents:
            line = line.strip()

            if go_on:
                if line.startswith('['):
                    go_on = False
                    line = line+"\n"
                    file_content_new.append(line)
                if line == old_entry:
                    line = new_entry+"\n"
                    file_content_new.append(line)
                else:
                    line = line+"\n"
                    file_content_new.append(line)
            elif line.startswith(self.tipo):
                go_on = True
                line = line+"\n"
                file_content_new.append(line)
            else:
                line = line+"\n"
                file_content_new.append(line)

        fpattern = self.open_patterns(operation='w')
        fpattern.writelines(file_content_new)
        fpattern.flush()
        fpattern.close()
