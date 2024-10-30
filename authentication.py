#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pylint: disable=W1203
# pylint: disable=W0613

'''
   ICE Gauntlet Token Server
'''

import sys
import json
import random
import signal
import string
import logging
import os.path
import glob, os
import random
import uuid
import manage_services

import Ice
Ice.loadSlice('iceflix.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceFlix
import IceStorm

USERS_FILE = 'users.json'
PASSWORD_HASH = 'password_hash'
CURRENT_TOKEN = 'current_token'
TOKEN_SIZE = 40

authenticators = {}
streamings = {}
catalogs = {}


def _build_token_():
    valid_chars = string.digits + string.ascii_letters
    return ''.join([random.choice(valid_chars) for _ in range(TOKEN_SIZE)])


class Authenticator(IceFlix.Authenticator):
    '''Authentication servant'''
    def __init__(self, publisher_availability, adapter):
        self._users_ = {}
        self._active_tokens_ = set()
        if os.path.exists(USERS_FILE):
            self.refresh()
        else:
            self.__commit__()

        self.service_manager = manage_services.ManageServices()

        sync_services = IceFlix.ServiceAvailabilityPrx.uncheckedCast(publisher_availability)

        proxy = adapter.addWithUUID(self)
        this_authenticator = IceFlix.AuthenticatorPrx.checkedCast(proxy)
        auth_id = str(uuid.uuid4())

        sync_services.authenticationService(this_authenticator, auth_id)

    def get_show_services(self, dict_of_catalogs, dict_of_auth, dict_of_streams):
        authenticators = dict_of_auth
        streamings = dict_of_streams
        catalogs = dict_of_catalogs

    def refresh(self, *args, **kwargs):
        '''Reload user DB to RAM'''
        logging.debug('Reloading user database')
        with open(USERS_FILE, 'r') as contents:
            self._users_ = json.load(contents)
        self._active_tokens_ = set([
            user.get(CURRENT_TOKEN, None) for user in self._users_.values()
        ])

    def __commit__(self):
        logging.debug('User database updated!')
        with open(USERS_FILE, 'w') as contents:
            json.dump(self._users_, contents, indent=4, sort_keys=True)

    def changePassword(self, user, currentPassHash, newPassHash, current=None):
        '''Set/Change user password'''
        logging.debug(f'Change password requested by {user}')
        if user not in self._users_:
            raise IceFlix.Unauthorized()
        current_hash = self._users_[user].get(PASSWORD_HASH, None)
        if current_hash is None:
            # User auth is empty
            self._users_[user][CURRENT_TOKEN] = _build_token_()
        else:
            if current_hash != currentPassHash:
                raise IceFlix.Unauthorized()
        self._users_[user][PASSWORD_HASH] = newPassHash
        self.__commit__()

    def refreshAuthorization(self, user, passwordHash, current=None):
        '''Create new auth token'''
        logging.debug(f'New token requested by {user}')
        if user not in self._users_:
            raise IceFlix.Unauthorized()
        current_hash = self._users_[user].get(PASSWORD_HASH, None)
        if not current_hash:
            # User auth is empty
            raise IceFlix.Unauthorized()
        if current_hash != passwordHash:
            raise IceFlix.Unauthorized()

        current_token = self._users_[user].get(CURRENT_TOKEN, None)
        if current_token:
            # pylint: disable=W0702
            try:
                self._active_tokens_.remove(current_token)
            except:
                # Token is already inactive!
                pass
            # pylint: enable=W0702
        new_token = _build_token_()
        self._users_[user][CURRENT_TOKEN] = new_token
        self.__commit__()
        self._active_tokens_.add(new_token)
        return new_token

    def isAuthorized(self, authentication, current=None):
        '''Return if token is active'''

        for user in self._users_:
            if self._users_[user][CURRENT_TOKEN] == authentication:
                return True
        return False

class Server(Ice.Application):
    '''
    Authentication Server
    '''
    def run(self, args):
        '''
        Server loop
        '''
        logging.debug('Initializing server...')

        #SERVICE AVAILABILITY SUSCRIPTION
        proxy = self.communicator().propertyToProxy('IceFlix.IceStorm/TopicManager')

        topic_mgr = IceStorm.TopicManagerPrx.checkedCast(proxy) #pylint: disable=E1101
        if not topic_mgr:
            print ('Invalid proxy')
            return 2

        topic_name_availability = "ServiceAvailability"
        qos={}

        try:
            topic_availability = topic_mgr.retrieve(topic_name_availability)# pylint: disable=W0702
        except:# pylint: disable=W0702
            topic_availability = topic_mgr.create(topic_name_availability)# pylint: disable=W0702

        publisher_availability = topic_availability.getPublisher()

        adapter = self.communicator().createObjectAdapter('AuthenticationAdapter')

        servant = Authenticator(publisher_availability, adapter)

        subscriber = adapter.addWithUUID(servant)
        topic_availability.subscribeAndGetPublisher(qos, subscriber)

        signal.signal(signal.SIGUSR1, servant.refresh)

        proxy = adapter.add(servant, self.communicator().stringToIdentity('default'))
        adapter.addDefaultServant(servant, '')
        adapter.activate()
        logging.debug('Adapter ready, servant proxy: {}'.format(proxy))
        print('"{}"'.format(proxy), flush=True)


        logging.debug('Initializing server...')
        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()

        topic_availability.unsubscribe(subscriber)

        return 0


if __name__ == '__main__':
    app = Server()
    sys.exit(app.main(sys.argv))
