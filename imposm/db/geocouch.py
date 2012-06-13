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
                "osm_id": data['osm_id'],
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
        spatial_funs = {}
        for mapping in mappings:
            spatial_funs[mapping.name] = self.spatial_fun([mapping.name])
        designdoc = {'spatial': spatial_funs}

        conn = httplib.HTTPConnection(self.db_conf.host, self.db_conf.port)
        conn.request('PUT', '/' + self.db_conf.db + '/_design/imposm',
                     json.dumps(designdoc))
        resp = conn.getresponse().read()

    def spatial_fun(self, mapping_names):
        condition = []
        for name in mapping_names:
            condition.append(
                "(doc.mapping_names.indexOf('" + name + "') !== -1)")
        return ("function(doc) {if (doc.geometry && (" +
                "||".join(condition) + ")) {"
                "delete doc.mapping_names; emit(doc.geometry, doc);}}")

    def swap_tables(self, new_prefix, existing_prefix, backup_prefix):
        raise NotImplementedError

    def remove_tables(self, prefix):
        raise NotImplementedError

    def remove_views(self, prefix):
        raise NotImplementedError

    def create_views(self, mappings, ignore_errors=False):
        spatial_funs = {}
        for mapping in mappings.values():
            if isinstance(mapping, UnionView):
                mapping_names = [m.name for m in mapping.mappings]
                spatial_funs[mapping.name] = self.spatial_fun(mapping_names)

        # Create_tables already created a design document, merge the new
        # indexes with the existing one
        conn = httplib.HTTPConnection(self.db_conf.host, self.db_conf.port)
        conn.request('GET', '/' + self.db_conf.db + '/_design/imposm')
        designdoc = json.loads(conn.getresponse().read())
        revision = designdoc['_rev']
        designdoc['spatial'].update(spatial_funs)
        conn.request(
            'PUT', '/' + self.db_conf.db + '/_design/imposm?rev=' + revision,
            json.dumps(designdoc))
        resp = conn.getresponse().read()

    def create_generalized_tables(self, mappings):
        # For now, this backend doesn't support generalized tables
        pass

    def optimize(self, mappings):
        raise NotImplementedError
