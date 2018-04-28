#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

from girder import events
from girder.api import access
from girder.api.describe import Description
from girder.api.rest import Resource
from .settings import ImageSpaceSetting

import json
import requests

setting = ImageSpaceSetting()


class ImageSearch(Resource):
    def __init__(self):
        self.resourceName = 'imagesearch'
        self.route('GET', (), self.getImageSearch)

    @access.public
    def getImageSearch(self, params):
        return self._imageSearch(params)

    @access.public
    def postImageSearch(self, params):
        return self._imageSearch(params)

    def _imageSearch(self, params):
        print("Hello World!")
        limit = params['limit'] if 'limit' in params else '100'
        query = params['query'] if 'query' in params else '*:*'
        offset = params['offset'] if 'offset' in params else '0'
        classifications = json.loads(params['classifications']) if 'classifications' in params else []
        base = setting.get('IMAGE_SPACE_SOLR') + '/select'

        if classifications:
            query += ' AND (%s)' % ' OR '.join(['%s:[.7 TO *]' % key
                                                for key in classifications])

        qparams = {
            'wt': 'json',
            'hl': 'true',
            'hl.fl': '*',
            'q': query,
            'start': offset,
            'rows': limit
        }

        # Give plugins a chance to adjust the Solr query parameters
        event = events.trigger('imagespace.imagesearch.qparams', qparams)
        for response in event.responses:
            qparams = response

        try:
            result = requests.get(base, params=qparams, verify=False).json()
        except ValueError:
            return []

        try:
            for image in result['response']['docs']:
                image['highlight'] = result['highlighting'][image['id']]
        except KeyError:
            return {
                'numFound': 0,
                'docs': []
            }

        response = {
            'numFound': result['response']['numFound'],
            'docs': result['response']['docs']
        }

        # Give plugins a chance to adjust the end response of the imagesearch
        event = events.trigger('imagespace.imagesearch.results', response)
        for eventResponse in event.responses:
            response = eventResponse

        return response
    getImageSearch.description = Description('Searches image database')
    # @todo document params
