from django.http import HttpResponse
from django.utils import simplejson
from resteasy.specifications.models import Specification
from resteasy.specifications.models import Resource
from resteasy.specifications.models import Property

def index(request):
    response = __get_index_response(request)
    return HttpResponse(response, mimetype='application/json')

def __get_index_response(request):
    response_properties = []
    
    spec_models = Specification.objects.all()
    versions = __get_versions(spec_models)
    
    for spec in versions.keys():
        spec_properties = dict(name=spec, versions=versions[spec])
        response_properties.append(spec_properties)
    
    if len(response_properties) == 0:
        error_description = "There are no specifications defined in the system."
        response = __create_error_response(request, error_description)
    else:
        response = simplejson.dumps(response_properties)
        
    return response

def __get_versions(spec_models):
    versions = {}
    for spec_model in spec_models:
        if versions.has_key(spec_model.name):
            versions[spec_model.name].append(spec_model.version)
        else:
            versions[spec_model.name] = [spec_model.version]
            
    return versions
    
def resources(request, specification, version):
    try:
        response = __get_resources_response(request, specification, version)
    except (Specification.DoesNotExist):
        error_description = ("Specification '" + specification + ":" + version 
                            + "' does not exist.")
        response = __create_error_response(request, error_description)
        
    return HttpResponse(response,
                        mimetype='application/json')
    
def __get_resources_response(request, specification, version):
    spec = Specification.objects.get(name=specification, version=version)
    resources = Resource.objects.filter(specification=spec)
        
    if len(resources) > 0:
        response_properties = [resource.get_properties() for resource in resources]
        response = simplejson.dumps(response_properties)
    else:
        error_description = ("There are no resources defined for the specification " 
                                + specification + ":" + version)
        response = __create_error_response(request, error_description)
    
    return response
    
def resource(request, resource_id):
    try:
        response = __get_resource_response(request, resource_id)    
    except (Resource.DoesNotExist):
        error_description = ("Resource with id: '" + resource_id 
                             + "' does not exist.")
        response = __create_error_response(request, error_description)
    else:        
        return HttpResponse(response, mimetype='application/json')
    
def __get_resource_response(request, resource_id):
    resource = Resource.objects.get(id=resource_id)
    property_models = Property.objects.filter(resource=resource)
        
    if len(property_models) > 0:
        response_properties = {}
        for property_model in property_models:
            id, properties = property_model.get_properties()
            response_properties[id] = properties
            
        response = simplejson.dumps(response_properties)
    else:
        error_description = ("There are no properties defined for the resource " 
                             + resource.url + " with id: " + resource.id)
        response = __create_error_response(request, error_description)
        
    return response

def __create_error_response(request, error_description):
    error_response_properties = {
                                 'error' : {
                                            'url' : request.path,
                                            'method' : request.method,
                                            'desciption' : error_description
                                           }
                                }
    
    return simplejson.dumps(error_response_properties)
    
