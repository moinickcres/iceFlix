#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pylint: disable=W1203
# pylint: disable=W0613

'''
   ICE Gauntlet Token Server
'''

#https://docs.python.org/3/library/cmd.html

import cmd, sys
from turtle import *
from getpass import getpass
import Ice
Ice.loadSlice('iceflix.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceFlix
import IceStorm

class IceFlixShell(cmd.Cmd):
    intro = 'Welcome to the shell.   Type help or ? to list commands.\n'
    prompt = '(IceFlixClient) '
    file = None

    # ----- basic turtle commands -----

    def __init__(self, proxy):
        super(IceFlixShell, self).__init__()

        self.proxy_main = proxy

        self.selected_media = None
        self.authentication = None
    
    def do_authentication(self):
        'Authentication of the user:  AUTHENTICATION <token>'
        user = input("User: \n")
        print("Password: \n")
        passwd = getpass()
        self.authentication = self.proxy_main.getAuthenticator.refreshAuthorization(user, passwd)

    def do_close(self):
        'Log out from the system:  CLOSE'
        self.authentication = NULL

    def do_searchID(self, argument):
        'Search for the different medias by the tile, the name, or the tags:  SEARCH <id/name/tags> <exact name/include all tags(Y or N)>'
        self.selected_media = self.proxy_main.getCatalogService.getTile(argument)

    def do_searchName(self, argument):
        'Search for the different medias by the tile, the name, or the tags:  SEARCH <id/name/tags> <exact name/include all tags(Y or N)>'
        preference = input("Exact name? Write y or n:\n")
        self.selected_media = self.proxy_main.getCatalogService.getTilesByName(argument, preference)

    def do_searchTags(self, argument):
        'Search for the different medias by the tile, the name, or the tags:  SEARCH <id/name/tags> <exact name/include all tags(Y or N)>'
        preference = input("Include all tags? Write y or n:\n")
        self.selected_media = self.proxy_main.getCatalogService.getTilesByTags(argument, preference)

    def do_editName(self, argument):
        'Edit the medias changing the tile name, the tags, or removing them:  EDIT <new name/tags to add/tags to remove>'
        #se tiene que haber elegido un media en el do_search para poder usar esta opción
        if self.selected_media == NULL:
            print("Select a video first")
        else:
            self.proxy_main.getCatalogService.renameTile(self.selected_media.id, argument, self.authentication)
        
    def do_addTags(self, argument):
        'Edit the medias changing the tile name, the tags, or removing them:  EDIT <new name/tags to add/tags to remove>'
        if self.selected_media == NULL:
            print("Select a video first")
        else:
            self.proxy_main.getCatalogService.addTags(self.selected_media.id, argument, self.authentication)
        
    def do_removeTags(self, argument):
        'Edit the medias changing the tile name, the tags, or removing them:  EDIT <new name/tags to add/tags to remove>'
        if self.selected_media == NULL:
            print("Select a video first")
        else:
            self.proxy_main.getCatalogService.removeTags(self.selected_media.id, argument, self.authentication)

    def do_play(self, token):
        'When the media is selected, reproduce the content:  PLAY <authentication>'
        if self.selected_media == NULL:
            print("Select a video first")
        else:
            streaming_service = self.proxy_main.media_list[self.selected_media.provider]
            self.stream = streaming_service.getStream(self.selected_media.id, token)
            self.stream.getSDP(token, 7777)

    def do_stop(self):
        'Stop de reproduction of the media:  STOP'
        self.stream.stop()

    def do_bye(self, arg):
        'Stop recording, close the window, and exit:  BYE'
        print('Thank you for using IceFlix')
        self.close()
        bye()
        return True

    # ----- record and playback -----
    def do_record(self, arg):
        'Save future commands to filename:  RECORD rose.cmd'
        self.file = open(arg, 'w')
    def do_playback(self, arg):
        'Playback commands from a file:  PLAYBACK rose.cmd'
        self.close()
        with open(arg) as f:
            self.cmdqueue.extend(f.read().splitlines())
    def precmd(self, line):
        line = line.lower()
        if self.file and 'playback' not in line:
            print(line, file=self.file)
        return line
    def close(self):
        if self.file:
            self.file.close()
            self.file = None


class IceFlixClient(Ice.Application):
    def run(self, argv):

        proxy_main = self.communicator().stringToProxy(argv[1])
        #COMO PASO UN ARGUMENTO DENTRO DEL SHELL?
        IceFlixShell(proxy_main).cmdloop()

def parse(arg):
    'Convert a series of zero or more numbers to an argument tuple'
    return tuple(map(int, arg.split()))

if __name__ == '__main__':
    app = IceFlixClient()
    sys.exit(app.main(sys.argv))
