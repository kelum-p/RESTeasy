'''
Created on Jul 31, 2011

@author: Coco
'''

from django.conf.urls.defaults import patterns

'''
API
GET:
hostname/specifications/ 
    -> shows all the specifications and their resources under each version
        [
            {
                "name": "config",
                "versions": [
                            "v1",
                            "v2",
                            "v3"
                            ]
            },
            ...
        ]
                        
                        
hostname/specifications/:spec_name/:version/resources 
    -> shows all the resources associated to a versioned specification
        [
            {
                "url": "config/v1/first",
                "id": "338a6cc36afc5ab36a18a7eed1d8c0cf"
                "headers" :
                    {
                        key : value
                        ...
                    },
                "elementsHref": "resource href to get properties"
            },
            {
                "url": "config/v1/second",
                "id": "90f71e690ccffc40f8f5cf139754252f"
                ...
            },
            ...
        ]

hostname/specifications/:resource_id/elements
    -> shows all the elements associated to a resource
        {
            "578a08534564542a9dd2f41b1d89fbaa": {
                "static": true,
                "required": true,
                "type": "string",
                "name": "child",
                "parent": "8b298e10b06ecf85ffeb75c74c670fbb"
            },
            "8b298e10b06ecf85ffeb75c74c670fbb": {
                "static": true,
                "required": true,
                "type": "object",
                "name": "parent"
            },
            ...
        }
    
POST:
hostname/specifications/specification
    -> creates a new specification
hostname/specification/resource
    -> creates a new resource
hostname/specification/elements
    -> creates a new element
'''

urlpatterns = patterns('specifications.views',
                       # GET resources
                       (r'^$', 'index'),
                       (r'^/(?P<specification>\w+)/(?P<version>\w+)/resources$', 'resources'),
                       (r'^/resource/(?P<resource_id>\w+)$', 'resource'),
                       (r'^/(?P<resource_id>\w+)/elements$', 'elements'),
                       
                       
                       # POST resources
                       (r'^/specification$', 'specification'),
                       (r'^/resource$', 'resource'),
                       (r'^/element$', 'element')
                      )
