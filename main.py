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

import manage_services

import Ice
Ice.loadSlice('iceflix.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceFlix
import IceStorm

authentication_list = {}
catalog_list = {}
media_list = {}

class MainI(IceFlix.Main):

    def getAuthenticator(self, current=None):
        try:
            return random.choice(list(authentication_list.values()))
        except:
            raise IceFlix.TemporaryUnavailable()

    def getCatalogService(self, current=None):
        try:
            return random.choice(list(catalog_list.values()))
        except:
            raise IceFlix.TemporaryUnavailable()

class ServiceAvailabilityI(IceFlix.ServiceAvailability):
    '''
    Synch for the services
    '''

    def __init__(self):
        self.service_manager = manage_services.ManageServices()

    def catalogService(self, service, id, current = None):
        catalog_list[id] = service
        print("New Catalog service: ", id)

        self.service_manager.announce_catalog_service(service, id, catalog_list, authentication_list, media_list)

    def authenticationService(self, service, id, current = None):
        authentication_list[id] = service
        print("New Authentication service: ", id)

        self.service_manager.announce_auth_service(service, id, catalog_list, authentication_list, media_list)

    def mediaService(self, service, id, current = None):
        media_list[id] = service
        print("New Media service: ", id)

        self.service_manager.announce_streaming_service(service, id, catalog_list, authentication_list, media_list)


class Server(Ice.Application):
    '''
    Authentication Server
    '''
    def run(self, args):
        '''
        Server loop
        '''
        logging.debug('Initializing server...')
        servant = MainI()

        proxy = self.communicator().propertyToProxy('IceFlix.IceStorm/TopicManager')

        topic_mgr = IceStorm.TopicManagerPrx.checkedCast(proxy) #pylint: disable=E1101
        if not topic_mgr:
            print ('Invalid proxy')
            return 2

        topic_name = "ServiceAvailability"
        qos={}

        try:
            topic = topic_mgr.retrieve(topic_name)# pylint: disable=W0702
        except:# pylint: disable=W0702
            topic = topic_mgr.create(topic_name)# pylint: disable=W0702

        adapter = self.communicator().createObjectAdapter('MainAdapter')
        proxy = adapter.add(servant, self.communicator().stringToIdentity('default'))

        suscriber_servant = ServiceAvailabilityI()
        subscriber = adapter.addWithUUID(suscriber_servant)

        topic.subscribeAndGetPublisher(qos, subscriber)

        adapter.activate()

        logging.debug('Adapter ready, servant proxy: {}'.format(proxy))
        print('Main service: "{}"'.format(proxy), flush=True)

        logging.debug('Initializing server...')
        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()

        topic.unsubscribe(subscriber)

        return 0


if __name__ == '__main__':
    app = Server()
    sys.exit(app.main(sys.argv))