#!/usr/bin/env python3
# PYTHON_PREAMBLE_START_STANDARD:{{{

# Christopher David Cotton (c)
# http://www.cdcotton.com

# modules needed for preamble
import importlib
import os
from pathlib import Path
import sys

# Get full real filename
__fullrealfile__ = os.path.abspath(__file__)

# Function to get git directory containing this file
def getprojectdir(filename):
    curlevel = filename
    while curlevel is not '/':
        curlevel = os.path.dirname(curlevel)
        if os.path.exists(curlevel + '/.git/'):
            return(curlevel + '/')
    return(None)

# Directory of project
__projectdir__ = Path(getprojectdir(__fullrealfile__))

# Function to call functions from files by their absolute path.
# Imports modules if they've not already been imported
# First argument is filename, second is function name, third is dictionary containing loaded modules.
modulesdict = {}
def importattr(modulefilename, func, modulesdict = modulesdict):
    # get modulefilename as string to prevent problems in <= python3.5 with pathlib -> os
    modulefilename = str(modulefilename)
    # if function in this file
    if modulefilename == __fullrealfile__:
        return(eval(func))
    else:
        # add file to moduledict if not there already
        if modulefilename not in modulesdict:
            # check filename exists
            if not os.path.isfile(modulefilename):
                raise Exception('Module not exists: ' + modulefilename + '. Function: ' + func + '. Filename called from: ' + __fullrealfile__ + '.')
            # add directory to path
            sys.path.append(os.path.dirname(modulefilename))
            # actually add module to moduledict
            modulesdict[modulefilename] = importlib.import_module(''.join(os.path.basename(modulefilename).split('.')[: -1]))

        # get the actual function from the file and return it
        return(getattr(modulesdict[modulefilename], func))

# PYTHON_PREAMBLE_END:}}}


def shortcuttolist(string):
    hyphenword = 'THISISAPLUSthisisahyphen'
    string = string.replace('\-', hyphenword)
    
    shortcutlist = string.split('-')
    shortcutlist = [item.strip() for item in shortcutlist]
    shortcutlist = [item.replace(hyphenword, '-') for item in shortcutlist]

    return(shortcutlist)


def parseshortcuts(inputfile):
    import sys

    with open(inputfile, 'r', encoding = 'latin-1') as f:
        lines = f.read().splitlines()

    # Removing comments
    hashword = 'THISISAHASHthisisahash'
    mains = []
    starts = []
    originalpos = []
    for i in range(len(lines)):
        
        line = lines[i]

        # don't want to replace escaped hashes
        line = line.replace('\#', hashword)

        line = line.split('#')[0]

        line = line.replace(hashword, '#')

        linestripped = line.lstrip()

        start = line.replace(linestripped, '')

        if linestripped != '':
            mains.append(linestripped)
            starts.append(start)
            originalpos.append(i)

    # Getting level of line
    linelevels = []
    currentlevels = ['']
    # must be same as previous level or start with previous level
    for i in range(len(starts)):
        start = starts[i]

        level = None
        for j in reversed(range(len(currentlevels))):
            if currentlevels[j] in start:
                extratext = start.replace(currentlevels[j], '', 1)

                if extratext == '':
                    level = j
                    currentlevels = currentlevels[0: j + 1]
                else:
                    level = j + 1
                    currentlevels = currentlevels[0: j + 1] + [start]
                
                break

        if level is not None:
            linelevels.append(level)
        else:
            print('Line number ' + str(originalpos[i]) + ' has an error in the levels')
            print('Original line:')
            print(lines[originalpos[i]])
            sys.exit(1)

    shortcuts = []
    keychains = []
    for i in range(0, len(mains)):
        if i != len(mains) - 1 and linelevels[i] < linelevels[i + 1]:
            keyshortcut = importattr(__projectdir__ / Path('shortcuts_func.py'), 'shortcuttolist')(mains[i])
            keychains = keychains[0: linelevels[i]] + [keyshortcut]
        else:
            # Remove levels if necessary i.e. if now 0 and was 1 before, want to get rid of prior keychain
            keychains = keychains[0: linelevels[i]]

            splitmain = mains[i].split(' : ') 

            if len(splitmain) != 2:
                print('Line number ' + str(originalpos[i]) + ' should have exactly one " : "')
                print('Original line:')
                print(lines[originalpos[i]])
                sys.exit(1)


            keyshortcut = importattr(__projectdir__ / Path('shortcuts_func.py'), 'shortcuttolist')(splitmain[0])

            command = splitmain[1].strip()

            shortcuts.append([keychains, keyshortcut, command])

    return(shortcuts)


def parsetoopenbox(inputfile):
    shortcuts = importattr(__projectdir__ / Path('shortcuts_func.py'), 'parseshortcuts')(inputfile)

    outputlist = []

    oldkeychain = []
    for item in shortcuts:
        keychain = item[0]

        commonelements = []
        for j in range(min([len(oldkeychain), len(keychain)])):
            if oldkeychain[j] == keychain[j]:
                commonelements.append(keychain[j])
            else:
                break

            
        # closing old keychains
        for j in reversed(range(len(commonelements), len(oldkeychain))):
            keychainend = ' ' * 2 * j + '</keybind>'
            outputlist.append(keychainend)

        # opening new keychains
        for j in range(len(commonelements), len(keychain)):
            keychainstart = ' ' * 2 * j + '<keybind key="' + '-'.join(keychain[j]) + '">'
            outputlist.append(keychainstart)


        # adding actual shortcuts:
        j = len(keychain)

        keychainstart = ' ' * 2 * j + '<keybind key="' + '-'.join(item[1]) + '">'
        outputlist.append(keychainstart)

        outputlist.append(' ' * 2 * (j + 1) + '<action name="Execute">')

        command = ' ' * 2 * (j + 2) + '<command>' + item[2] + '</command>'
        outputlist.append(command)
        
        outputlist.append(' ' * 2 * (j + 1) + '</action>')

        outputlist.append(' ' * 2 * j + '</keybind>')

        # update oldkeychain:
        oldkeychain = keychain

    # closing final keychain
    for j in reversed(range(0, len(oldkeychain))):
        keychainend = ' ' * 2 * j + '</keybind>'
        outputlist.append(keychainend)

    output = '\n'.join(outputlist)

    return(output)

