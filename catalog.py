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

medias = {}

authenticators = {}
streamings = {}
catalogs = {}

class MediaCatalog(IceFlix.MediaCatalog):

    def __init__(self, service_availability, adapter):
        self.service_manager = manage_services.ManageServices()

        sync_services = IceFlix.ServiceAvailabilityPrx.uncheckedCast(service_availability)
        
        proxy = adapter.addWithUUID(self)
        this_catalog = IceFlix.MediaCatalogPrx.checkedCast(proxy)
        catalog_id = str(uuid.uuid4())

        sync_services.catalogService(this_catalog, catalog_id)

    def get_show_services(self, dict_of_catalogs, dict_of_auth, dict_of_streams):
        authenticators = dict_of_auth
        streamings = dict_of_streams
        catalogs = dict_of_catalogs

        for auth in authenticators.items():
            print("New auth service: ", auth)

        for stream in streamings.items():
            print("New stream service: ", stream)

        for catalog in catalogs.items():
            print("New catalog service: ", catalog)

    def getTile(self, id):
        try:
            for media in medias:
                if media.id == id:
                    return media
        except:
            raise IceFlix.WrongMediaId(id)

    def getTilesByName(self, name, exact):
        if exact == "y":
            for media in medias:
                if media.info.name == name:
                    return media

        elif exact == "n": 
            for media in medias:
                if name in media.info.name:
                    return media

    def getTilesByTags(self, tags, includeAllTags):
        if includeAllTags == "y":
            for media in medias:
                if tags == media.info.tags:
                    return media

        elif includeAllTags == "n": 
            for media in medias:
                if tags in media.info.tags:
                    return media
 
    def renameTile(self, id, name, authentication):
        try:
            if random.choice(list(authenticators)).isAuthorized(authentication):
                try:
                    for media in medias:
                        if media.id == id:
                            media.info.name = name
                            return
                except:
                    raise IceFlix.WrongMediaId(id)
            else:
                raise IceFlix.Unauthorized()
        except:
            raise IceFlix.WrongMediaId(id)

    def addTags(self, id, tags, authentication):
        try:
            if random.choice(list(authenticators)).isAuthorized(authentication):
                try:
                    for media in medias:
                        if media.id == id:
                            media.info.tags = tags
                            return
                except:
                    raise IceFlix.WrongMediaId(id)
            else:
                raise IceFlix.Unauthorized()
        except:
            raise IceFlix.TemporaryUnavailable()

    def removeTags(self, id, tags, authentication):
        try:
            if random.choice(list(authenticators)).isAuthorized(authentication):
                try:
                    for media in medias:
                        if media.id == id:
                            if tags in media.info.tags:
                                media.info.tags.remove(tags)
                                return
                except:
                    raise IceFlix.WrongMediaId(id)
            else:
                raise IceFlix.Unauthorized()
        except:
            raise IceFlix.TemporaryUnavailable()


class StreamAnnouncesI(IceFlix.StreamAnnounces):
    #aqui se supone que cada uno de estos servicios se crea su json temporal con la info del catalogo, pero para que? si luego se va a borrar
    #y aqui tiene una lista igual?
    #o es que es un json para todos que se actualiza con todos los servicios y luego lo leen y lo modifican en los metodos de arriba?
    def newMedia(self, id, initialName, providerId, current=None):
        
        media = IceFlix.Media()
        info = IceFlix.MediaInfo()
        media.id = id
        media.provider = providerId
        
        info.name = initialName
        info.tags = []
        media.info = info

        medias[id].append(media)


class Server(Ice.Application):
    '''
    Authentication Server
    '''
    def run(self, argv):
        '''
        Server loop
        '''
        logging.debug('Initializing server...')

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

        adapter = self.communicator().createObjectAdapter('CatalogAdapter')

        suscriber_servant = StreamAnnouncesI()
        subscriber = adapter.addWithUUID(suscriber_servant)

        topic_announcement.subscribeAndGetPublisher(qos, subscriber)

        #SERVICE AVAILABILITY SUBSCRIPTION
        topic_name_availability = "ServiceAvailability"

        try:
            topic_availability = topic_mgr.retrieve(topic_name_availability)# pylint: disable=W0702
        except:# pylint: disable=W0702
            topic_availability = topic_mgr.create(topic_name_availability)# pylint: disable=W0702

        publisher_availability = topic_availability.getPublisher()

        servant = MediaCatalog(publisher_availability, adapter)

        #PROXY OF THE ACTUAL SERVER
        proxy = adapter.add(servant, self.communicator().stringToIdentity('default'))
        adapter.addDefaultServant(servant, '')

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