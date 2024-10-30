#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import random
import signal
import string
import logging
import os.path
from getpass import getpass

import Ice
Ice.loadSlice('iceflix.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceFlix

class Client(Ice.Application):

    def run(self, argv):

        broker = self.communicator()
        proxy = broker.stringToProxy(argv[3])
        self.authentication = IceFlix.AuthenticatorPrx.checkedCast(proxy)

        user = argv[2]
        option = argv[1]

        if option == "-t":

            print("Enter password:")
            passwd = getpass()

            if passwd == "":
                token = self.authentication.refreshAuthorization(user, None)
            
            else :
                token = self.authentication.refreshAuthorization(user, passwd)
            
            print(token)

        elif option == "-p":

            print("Enter password:")
            passwd = getpass()
            print("Enter new password:")
            new_passwd = getpass()
            if new_passwd == "":
                self.authentication.changePassword(user, None, getpass())
            else:
                self.authentication.changePassword(user, passwd, new_passwd)

        return 0

sys.exit(Client().main(sys.argv))