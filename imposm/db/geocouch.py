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
        designdoc = '''{"language":"javascript","lists":{"json":"/**\n* This function outputs a GeoJSON FeatureCollection (compatible with\n* OpenLayers). JSONP requests are supported as well.\n*\n* @author Volker Mische\n*/\nfunction(head, req) {\n    var row, out, sep = '\\n';\n\n    // Send the same Content-Type as CouchDB would\n    if (req.headers.Accept.indexOf('application/json')!=-1) {\n        start({\"headers\":{\"Content-Type\" : \"application/json\"}});\n    }\n    else {\n        start({\"headers\":{\"Content-Type\" : \"text/plain\"}});\n    }\n\n    if ('callback' in req.query) {\n        send(req.query['callback'] + \"(\");\n    }\n\n    send('{\"type\": \"FeatureCollection\", \"features\":[');\n    while (row = getRow()) {\n    if((!req.query.mapping_name)||(row.value.mapping_names.indexOf(req.query.mapping_name)>-1)){\n        out = JSON.stringify({type: \"Feature\", geometry: row.geometry,\n                properties: row.value.properties});\n        send(sep + out);\n        sep = ',\\n';\n    }}\n    send(\"]}\");\n\n    if ('callback' in req.query) {\n        send(\")\");\n    }\n};\n"},"rewrites":[{"to":"/_show/tile/*","from":"/tile/*"},{"to":"/_spatiallist/full/*","from":"/json/*"}],"shows":{"tile":"function(doc, req){\n\tvar params=req.id.split(\"/\")\n\tvar loc = \"json?mapping_name=\"+params[0]+\"&bbox=\"+tile(params[1],params[2],params[3])\n\tfunction(doc) {\n  \t\treturn {\"code\": 302, \"body\": \"See other\", \"headers\": {\"Location\": loc}};\n\t}\n\t\n\t\n\t\n\tfunction tile(zz,xx,yy){\n\t\tfunction lng(x,z) {\n\t  \t\treturn (x/Math.pow(2,z)*360-180);\n\t \t}\n\t \tfunction lat(y,z) {\n\t  \t\tvar n=Math.PI-2*Math.PI*y/Math.pow(2,z);\n\t  \t\treturn (180/Math.PI*Math.atan(0.5*(Math.exp(n)-Math.exp(-n))));\n\t \t}\n\t var out=[lng(xx,zz),function lat(yy+1,zz),lng(xx+1,zz),function lat(yy,zz)]\n\t return out.join(\",\");\n\t}\n}\n"},"spatial":{"full":"function (doc){\nif(doc.geometry){\nemit(doc.geometry, doc);\n}\n}\n"}}'''
        conn = httplib.HTTPConnection(self.db_conf.host, self.db_conf.port)
        conn.request('PUT', '/' + self.db_conf.db + '/_design/imposm',
                     designdoc)
        resp = conn.getresponse().read()

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
