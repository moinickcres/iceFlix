#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pylint: disable=W1203
# pylint: disable=W0613

'''
   ICE Gauntlet Token Server
'''
import os
import shutil
import json
import random
from threading import Timer

class ManageServices:
    '''
    Method without ice things to manage the new rooms
    '''

    def announce_catalog_service(self, service, id, dict_of_catalogs, dict_of_auth, dict_of_streams):
        '''
        Get specific room
        '''
        service.get_show_services(dict_of_catalogs, dict_of_auth, dict_of_streams)
        
    def announce_streaming_service(self, service, id, dict_of_catalogs, dict_of_auth, dict_of_streams):
        '''
        Get specific room
        '''
        service.get_show_services(dict_of_catalogs, dict_of_auth, dict_of_streams)

    def announce_auth_service(self, service, id, dict_of_catalogs, dict_of_auth, dict_of_streams):
        '''
        Get specific room
        '''
        service.get_show_services(dict_of_catalogs, dict_of_auth, dict_of_streams)