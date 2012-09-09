# Copyright 2012 Omniscale (http://omniscale.com)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import json

import shapely
import urllib2
import httplib

import logging
log = logging.getLogger(__name__)

from imposm import config
from imposm.mapping import UnionView

class GeoCouchDB(object):
    insert_data_format = 'dict'

    def __init__(self, db_conf):
        self.db_conf = db_conf

    def commit(self):
        # There are not commits in CouchDB
        # Perhaps we could build up (query) the spatial indexes here
        pass

    def insert(self, insert_data, tries=0):
        geojsons = []
        for data in insert_data:
            geojsons.append({
                "_id": str(data['osm_id']),
                "mapping_names": data['mapping_names'],
                "geometry": data['geometry'],
                "properties": data['fields'],
            })

        json_blob = json.dumps({'docs': geojsons})
        conn = httplib.HTTPConnection(self.db_conf.host,
                                      self.db_conf.port)
        conn.request('POST', '/' + self.db_conf.db + '/_bulk_docs',
                     json_blob, {'Content-type': 'application/json'})
        resp = conn.getresponse().read()

    def geom_wrapper(self, geom):
        return shapely.geometry.mapping(geom)

    def reconnect(self):
        # Not needed for CouchDB
        pass

    def create_tables(self, mappings):
      pass

    def swap_tables(self, new_prefix, existing_prefix, backup_prefix):
        raise NotImplementedError

    def remove_tables(self, prefix):
        raise NotImplementedError

    def remove_views(self, prefix):
        raise NotImplementedError

    def create_views(self, mappings, ignore_errors=False):
        #don't need to wory about this here
        pass

    def create_generalized_tables(self, mappings):
        # For now, this backend doesn't support generalized tables
        pass

    def optimize(self, mappings):
        raise NotImplementedError
