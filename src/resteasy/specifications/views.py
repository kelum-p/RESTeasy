from StringIO import StringIO
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from resteasy.specifications.models import Specification
from resteasy.specifications.models import Resource
from resteasy.specifications.models import Property

class InvalidRequest(Exception):
    def __init__(self, request, status, message):
        self.request = request
        self.status = status
        self.message = message
    
    def __str__(self):
        return self.message
    
    def get_response(self):
        properties = {
                      'error' : {
                                 'url' : self.request.path,
                                 'method' : self.request.method,
                                 'message' : self.message
                                 }
                     }
        return self.status, simplejson.dumps(properties)

# Views for Specifications
def index(request):
    try:
        status = '200'
        response = _get_index_response(request)
    except InvalidRequest as invalid_request:
        status, response = invalid_request.get_response()
    finally:
        return _reply(status, response)

def _get_index_response(request):
    response_properties = []
    
    spec_models = Specification.objects.all()
    versions = _get_versions(spec_models)
    
    for spec in versions.keys():
        spec_properties = dict(name=spec, versions=versions[spec])
        response_properties.append(spec_properties)
    
    if len(response_properties) == 0:
        error_message = "No specifications defined in the system."
        raise InvalidRequest(request, '404', error_message)
    else:
        response = simplejson.dumps(response_properties)
        
    return response

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
    try:
        if request.method == 'POST':
            status = '200'
            response = _create_specification(request)
        else:
            error_message = "Only POST is supported."
            raise InvalidRequest(request, '400', error_message)
    except InvalidRequest as invalid_request:
        status, response = invalid_request.get_response()
    finally:    
        return _reply(status, response)

def _create_specification(request):
    try:
        specification_data = _get_post_data(request)
        return _parse_and_save_specification(request,
                                             specification_data)
    except InvalidRequest as invalid_request:
        raise invalid_request

def _parse_and_save_specification(request, specification_data):
    try:
        name = specification_data['name']
        version = specification_data['version']
        
        if name == None or len(name) <= 0:
            error_message = "name cannot be null or empty"
            raise InvalidRequest(request, '400', error_message)
        
        if version == None or len(version) <= 0:
            error_message = "version cannot be null or empty"
            raise InvalidRequest(request, '400', error_message)
                
        spec = Specification(name=name, version=version)
        _save_model(spec)
        return simplejson.dumps(spec.get_properties())
    except KeyError as key_error:
        error_message = "Missing required key: %s" % key_error
        raise InvalidRequest(request, '400', error_message)
        
# Views for Resources    
def resources(request, specification, version):
    try:
        status = '200'
        response = _get_resources_response(request, specification, version)
    except InvalidRequest as invalid_request:
        status, response = invalid_request.get_response()
    finally:
        return _reply(status, response)
    
def _get_resources_response(request, specification, version):
    try:
        spec = Specification.objects.get(name=specification, version=version)
    except Specification.DoesNotExist:
        error_message = ("Specification '" + specification + ":" + version 
                            + "' does not exist.")
        raise InvalidRequest(request, '404', error_message)
    else:
        resources = Resource.objects.filter(specification=spec)
            
        if len(resources) > 0:
            response_properties = [resource.get_properties() 
                                   for resource in resources]
            return simplejson.dumps(response_properties)
        else:
            error_message = ("No resources defined for the specification " 
                             + specification + ":" + version)
            raise InvalidRequest(request, '404', error_message)            

@csrf_exempt   
def resource(request, resource_id=None):
    try:
        status = '200'
        if request.method == 'POST':
            response = _create_resource(request)
        elif request.method == 'GET':
            resource = _get_resource(request, resource_id)
            resource_properties = resource.get_properties()
            response = simplejson.dumps(resource_properties)
        else:
            error_message = "Only POST and GET are supported"
            raise InvalidRequest(request, '400', error_message)
    except InvalidRequest as invalid_request:
        status, response = invalid_request.get_response()
    finally:
        return _reply(status, response)
        
def _create_resource(request):
    resource_data = _get_post_data(request)
    return _parse_and_save_resource(request, resource_data)
        
def _parse_and_save_resource(request, resource_data):
    try:
        specification = resource_data['specName']
        version = resource_data['specVersion']
        url = resource_data['url']
        
        spec = Specification.objects.get(name=specification, version=version)
        resource = Resource(url=url, specification=spec)
        _save_model(resource)
        return simplejson.dumps(resource.get_properties())
    except Specification.DoesNotExist:
        error_message = ("Specified specification '%s (%s)' does not exist" 
                        % (specification, version))
        raise InvalidRequest(request, '400', error_message)
    except KeyError as key_error:
        error_message = "Missing required key: %s" % key_error
        raise InvalidRequest(request, '400', error_message)

def properties(request, resource_id):
    try:
        status = '200'
        if resource_id:
            response = _get_properties(request, resource_id)
        else:
            error_message = "Must specify a resource id"
            raise InvalidRequest(request, '400', error_message)
    except InvalidRequest as invalid_request:
        status, response = invalid_request.get_response()
    finally:
        return _reply(status, response)

def _get_properties(request, resource_id): 
    resource = _get_resource(request, resource_id)          
    property_models = Property.objects.filter(resource=resource)
    if len(property_models) > 0:
        property_model_properties = {}
        for property_model in property_models:
            id, properties = property_model.get_properties()
            property_model_properties[id] = properties
                
        return simplejson.dumps(property_model_properties)
    else:
        error_message = ("Properties not found for resource with id %s" 
                        % (resource_id))
        raise InvalidRequest(request, '404', error_message)
        
def _get_resource(request, resource_id):
    try:    
        return Resource.objects.get(id=resource_id)
    except Resource.DoesNotExist:
        error_message = ("Resource with id: '" + resource_id 
                         + "' does not exist.")
        raise InvalidRequest(request, '404', error_message)
    
@csrf_exempt
def property(request):
    try:
        if request.method == 'POST':
            status = '200'
            response = _create_property(request)
        else:
            error_message = "Only POST is supported"
            raise InvalidRequest(request, '400', error_message)
    except InvalidRequest as invalid_request:
        status, response = invalid_request.get_response()
        
    return _reply(status, response)

def _create_property(request):
    property_data = _get_post_data(request)
    return _parse_and_save_property(request, property_data)

def _parse_and_save_property(request, property_data):
    try:
        resource_id = property_data['resource_id']
        resource = Resource.objects.get(id=resource_id)
        
        name = property_data['name']
        type = property_data['type']
        is_required = True
        is_static = True
        
        parent = None
        if property_data.has_key('parent_id'):
            parent = _get_property(request, property_data['parent_id'])
    except Resource.DoesNotExist:
        error_message = "Resource with ID '%s' does not exist" % resource_id
        raise InvalidRequest(request, '400', error_message)
    except KeyError as key_error:
        error_message = "Missing required key: %s" % key_error
        raise InvalidRequest(request, '400', error_message)
    else:
        if property_data.has_key('required'):
            is_required = property_data['required']
        
        if property_data.has_key('static'):
            is_static = property_data['static']
        
        property = Property(name=name,
                            type=type,
                            is_required=is_required,
                            is_static=is_static,
                            resource=resource,
                            parent=parent
                           )
        _save_model(property)
        return ":)"

def _get_property(request, property_id):
    try:
        return Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        error_message = "Property with id '%s' does not exist" % property_id
        raise InvalidRequest(request, '400', error_message)

def _save_model(model):
    model.generate_id()
    model.save()

def _get_post_data(request):
    data_stream = StringIO(request.raw_post_data)
    try:
        data = simplejson.load(data_stream)
    except ValueError:
        error_message = "Invalid JSON post data to create a specification"
        raise InvalidRequest(request, '400', error_message)
    else:
        if isinstance(data, dict):
            return data
        else:
            error_message = "Root of JSON must be an type object"
            raise InvalidRequest(request, '400', error_message)

def _reply(status, response):
    mime_type = 'application/json'
    if status == '200':
        reply = HttpResponse(response, mime_type)
    elif status == '404':
        reply = HttpResponseNotFound(response, mime_type)
    elif status == '400':
        reply = HttpResponseBadRequest(response, mime_type)
    else:
        raise Exception("Reply status '%s' not supported" % status)
        
    return reply
    
