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
import hashlib
import uuid
import iceflixrtsp
import ipaddress
import manage_services

import Ice
Ice.loadSlice('iceflix.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceFlix
import IceStorm

authenticators = {}
streamings = {}
catalogs = {}

class StreamControllerI(IceFlix.StreamController):

    def __init__(self, file, service_manager):
        self.file = file
        self.service_manager = service_manager

    def getSDP(self, authentication, port, current=None):
        try:
            if (random.choice(list(authenticators)).isAuthorized(authentication) == False):
                    raise IceFlix.Unauthorized()
        except:
            raise IceFlix.TemporaryUnavailable()
        
        connection = current.con.getInfo()
        host_address = ipaddress.ip_address(connection.remoteAddress)
        host = str(host_address.ipv4_mapped)

        self.rtsp = iceflixrtsp.RTSPEmitter(self.file, host, port)
        self.rtsp.start()

        self.player = iceflixrtsp.RTSPPlayer()
        self.player.play(self.rtsp.sdp)

    #def getSyncTopic(self, current=None):

    #def refreshAuthentication(self, authentication, current=None):

    def stop(self, current=None):
        self.player.stop()
        self.rtsp.stop()

class StreamProvider(IceFlix.StreamProvider):

    def __init__(self, sync_catalog, publisher_availability, directory, adapter):
        self.media_list = {}
        self.new_stream_controller = None
        self.sync_catalog = sync_catalog
        os.chdir(directory)

        proxy = adapter.addWithUUID(self)
        this_streaming = IceFlix.StreamProviderPrx.checkedCast(proxy)
        streaming_id = str(uuid.uuid4())

        for (dirpath, dirnames, filenames) in os.walk("."):
            for file in filenames:
                with open(file, "rb") as f:
                    bytes = f.read()
                    readable_hash = hashlib.sha256(bytes).hexdigest()
                
                sync_catalog.newMedia(readable_hash, file, streaming_id)
                self.media_list[readable_hash] = file

        self.service_manager = manage_services.ManageServices()

        sync_services = IceFlix.ServiceAvailabilityPrx.uncheckedCast(publisher_availability)
       
        sync_services.mediaService(this_streaming, streaming_id)

    def get_show_services(self, dict_of_catalogs, dict_of_auth, dict_of_streams):
        authenticators = dict_of_auth
        streamings = dict_of_streams
        catalogs = dict_of_catalogs

    def getStream(self, id, authentication, current):
        try:
            if (random.choice(list(authenticators)).isAuthorized(authentication) == False):
                raise IceFlix.Unauthorized()
        except:
            raise IceFlix.TemporaryUnavailable()

        try:
            servant = StreamControllerI(self.media_list[id], self.service_manager)
            proxy = current.adapter.addWithUUID(servant)
            if self.new_stream_controller is None:
                self.new_stream_controller = IceFlix.StreamControllerPrx.checkedCast(proxy)
                return self.new_stream_controller
        except:
            raise IceFlix.WrongMediaId(id)

    def isAvailable(self, id, current=None):
        for file in self.media_list:
            if id == file:
                return True

    def reannounceMedia(self, current=None):
        for media in self.media_list:
            self.sync_catalog.newMedia(media, self.media_list[media], self)

class Server(Ice.Application):
    '''
    Authentication Server
    '''
    def run(self, argv):
        '''
        Server loop
        '''
        logging.debug('Initializing server...')

        directory = argv[1]

        #MEDIA ANNOUNCEMENT SUBSCRIPTION
        proxy = self.communicator().propertyToProxy('IceFlix.IceStorm/TopicManager')

        topic_mgr = IceStorm.TopicManagerPrx.checkedCast(proxy) #pylint: disable=E1101
        if not topic_mgr:
            print ('Invalid proxy')
            return 2

        topic_name_announcement = "MediaAnnouncement"
        qos={}

        try:
            topic_announcement = topic_mgr.retrieve(topic_name_announcement)# pylint: disable=W0702
        except:# pylint: disable=W0702
            topic_announcement = topic_mgr.create(topic_name_announcement)# pylint: disable=W0702

        publisher_announcement = topic_announcement.getPublisher()
        sync_catalog = IceFlix.StreamAnnouncesPrx.uncheckedCast(publisher_announcement)

        adapter = self.communicator().createObjectAdapter('StreamingAdapter')

        #SERVICE AVAILABILITY SUSCRIPTION
        topic_name_availability = "ServiceAvailability"

        try:
            topic_availability = topic_mgr.retrieve(topic_name_availability)# pylint: disable=W0702
        except:# pylint: disable=W0702
            topic_availability = topic_mgr.create(topic_name_availability)# pylint: disable=W0702

        publisher_availability = topic_availability.getPublisher()

        properties = self.communicator().getProperties()
        suscriber_servant = StreamProvider(sync_catalog, publisher_availability, directory, adapter)
        factory_id = properties.getProperty('StreamingFactoryIdentity')

        #PROXY OF THE ACTUAL SERVER
        proxy = adapter.add(suscriber_servant, self.communicator().stringToIdentity(factory_id))
        adapter.addDefaultServant(suscriber_servant, '')

        subscriber = adapter.addWithUUID(suscriber_servant)

        topic_announcement.subscribeAndGetPublisher(qos, subscriber)

        adapter.activate()

        logging.debug('Adapter ready, servant proxy: {}'.format(proxy))
        print('"{}"'.format(proxy), flush=True)


        logging.debug('Initializing server...')
        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()

        topic_announcement.unsubscribe(subscriber)

        return 0


if __name__ == '__main__':
    app = Server()
    sys.exit(app.main(sys.argv))