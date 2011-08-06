from StringIO import StringIO
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from resteasy.specifications.models import Specification
from resteasy.specifications.models import Resource
from resteasy.specifications.models import Property

# Views for Specifications
def index(request):
    status, response = _get_index_response(request)
    return _reply(status, response)

def _get_index_response(request):
    status = '200'
    response_properties = []
    
    spec_models = Specification.objects.all()
    versions = _get_versions(spec_models)
    
    for spec in versions.keys():
        spec_properties = dict(name=spec, versions=versions[spec])
        response_properties.append(spec_properties)
    
    if len(response_properties) == 0:
        error_message = "No specifications defined in the system."
        status, response = _create_404_error_response(request, error_message)
    else:
        response = simplejson.dumps(response_properties)
        
    return status, response

def _get_versions(spec_models):
    versions = {}
    for spec_model in spec_models:
        if versions.has_key(spec_model.name):
            versions[spec_model.name].append(spec_model.version)
        else:
            versions[spec_model.name] = [spec_model.version]
            
    return versions

@csrf_exempt
def specification(request):
    if request.method == 'POST':
        status, response = _create_specification(request)
    else:
        error_message = "Only POST is supported."
        status, response = _create_400_error_response(request, error_message)
        
    return _reply(status, response)

def _create_specification(request):
    status = '200'
    data_stream = StringIO(request.raw_post_data)
    try:
        specification_data = simplejson.load(data_stream)
        _parse_and_save_specification(request, specification_data)
    except ValueError:
        error_message = "Invalid JSON"
        status, response = _create_400_error_response(request, error_message)    
        
    return status, response

def _parse_and_save_specification(request, specification_data):
    if isinstance(specification_data, dict):
        try:
            name = specification_data['name']
            version = specification_data['version']
                
            _save_specification(name, version)
            status, response = ('200', ':)')
        except KeyError as exception:
            error_message = "Missing required key: %s" % exception
            status, response = _create_400_error_response(request, 
                                                          error_message)
    else:
        error_message = "Invalid JSON. The root must be a JSON object "
        status, response = _create_400_error_response(request, error_message)
        
    return status, response

def _save_specification(name, version):
    spec = Specification(name=name, version=version)
    spec.generate_id()
    spec.save()
 
# Views for Resources    
def resources(request, specification, version):
    try:
        status, response = _get_resources_response(request, 
                                                   specification, 
                                                   version)
    except Specification.DoesNotExist:
        error_message = ("Specification '" + specification + ":" + version 
                            + "' does not exist.")
        status, response = _create_404_error_response(request, error_message)
        
    return _reply(status, response)
    
def _get_resources_response(request, specification, version):
    status = '200'
    spec = Specification.objects.get(name=specification, version=version)
    resources = Resource.objects.filter(specification=spec)
        
    if len(resources) > 0:
        response_properties = [resource.get_properties() 
                               for resource in resources]
        response = simplejson.dumps(response_properties)
    else:
        error_message = ("No resources defined for the specification " 
                         + specification + ":" + version)
        status, response = _create_404_error_response(request, error_message)
    
    return status, response

@csrf_exempt    
def resource(request, resource_id=None):
    if request.method == 'POST':
        reply = HttpResponse("POST detected: " + request.raw_post_data)
    elif request.method == 'GET':
        if resource_id:
            reply = _get_resource(request, resource_id)
        else:
            error_message = "Must specify a resource id"
            status, response = _create_400_error_response(request, 
                                                          error_message)
            reply = _reply(status, response)
    else:
        error_message = "Only POST and GET are supported"
        status, response = _create_400_error_response(request, error_message)
        reply = _reply(status, response)
        
    return reply

def _create_resource(request):
    pass

def _get_resource(request, resource_id):
    try:
        status, response = _get_resource_response(request, resource_id)    
    except Resource.DoesNotExist:
        error_message = ("Resource with id: '" + resource_id 
                         + "' does not exist.")
        status, response = _create_404_error_response(request, error_message)
    else:        
        return _reply(status, response)
    
def _get_resource_response(request, resource_id):
    status = '200'
    resource = Resource.objects.get(id=resource_id)
    property_models = Property.objects.filter(resource=resource)
        
    if len(property_models) > 0:
        response_properties = {}
        for property_model in property_models:
            id, properties = property_model.get_properties()
            response_properties[id] = properties
            
        response = simplejson.dumps(response_properties)
    else:
        error_message = ("There are no properties defined for the resource " 
                         + resource.url + " with id: " + resource.id)
        status, response = _create_404_error_response(request, error_message)
        
    return status, response

def _create_400_error_response(request, error_message):
    response = _create_error_response(request, error_message)
    return '400', response

def _create_404_error_response(request, error_message):
    response = _create_error_response(request, error_message)
    return '404', response

def _create_error_response(request, error_message):
    error_response_properties = {
                                 'error' : {
                                            'url' : request.path,
                                            'method' : request.method,
                                            'message' : error_message
                                           }
                                }
    
    return simplejson.dumps(error_response_properties)

def _reply(status, response):
    mime_type = 'application/json'
    if status == '200':
        reply = HttpResponse(response, mime_type)
    elif status == '404':
        reply = HttpResponseNotFound(response, mime_type)
    elif status == '400':
        reply = HttpResponseBadRequest(response, mime_type)
    else:
        raise Exception("Reply status not supported")
        
    return reply
    
