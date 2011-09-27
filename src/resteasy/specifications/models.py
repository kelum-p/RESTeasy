from hashlib import md5
from django.db import models

class Specification(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    name = models.TextField()
    version = models.TextField()
    
    def generate_id(self):
        md5_hash = md5()
        md5_hash.update(self.name+self.version)
        self.id = md5_hash.hexdigest()
    
    def get_properties(self):
        return {
                'id' : self.id,
                'name' : self.name,
                'version': self.version
               }
    
    def __unicode__(self):
        return self.name
        
class Resource(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    url = models.TextField()
    specification = models.ForeignKey(Specification)
    
    def generate_id(self):
        md5_hash = md5()
        md5_hash.update(self.url+self.specification.id)
        self.id = md5_hash.hexdigest()
    
    def get_properties(self):
        return {
                'id' : self.id,
                'url' : self.url,
                'specName': self.specification.name, 
                'specVersion': self.specification.version,
                'elementsHref': '/specifications/%s/elements' % self.id
               }
     
    def __unicode__(self):
        return self.url
            
class Element(models.Model):
    id = models.TextField(primary_key=True)
    name = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=200)
    is_required = models.BooleanField(default=True);
    is_static = models.BooleanField(default=True);
    resource = models.ForeignKey(Resource)
    parent = models.ForeignKey('self', null=True, blank=True)
    
    def generate_id(self):
        tokens = [
                    self.id,
                    self.name,
                    self.resource.id,
                 ]
        
        if self.parent:
            tokens.append(self.parent.id)
            
        md5_input = "".join(token for token in tokens)
        md5_hash = md5()
        md5_hash.update(md5_input)
        self.id = md5_hash.hexdigest()
        
    def get_properties(self):
        elements = {
                      'id': self.id,
                      'name' : self.name,
                      'type' : self.type,
                      'required' : self.is_required,
                      'static' : self.is_static,
                     }
        
        if self.parent:
            elements['parent'] = self.parent.id
        
        return self.id, elements
    
    def __unicode__(self):
        tokens = [
                    self.name,
                    ": ",
                    self.type
                 ]
        
        if self.parent:
            tokens.extend([
                            " ^",
                            self.parent.name
                           ])
                                 
        return "".join([token for token in tokens])