import md5
from django.db import models

class Specification(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    name = models.TextField()
    version = models.TextField()
    
    def generate_id(self):
        self.id = md5.new(self.name+self.version).hexdigest()
    
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
        self.id = md5.new(self.url+self.specification.id).hexdigest()
    
    def get_properties(self):
        return {
                'id' : self.id,
                'url' : self.url,
                'specification': "%s (%s)" % 
                                (self.specification.name, 
                                 self.specification.version)
               }
     
    def __unicode__(self):
        return self.url
            
class Property(models.Model):
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
        self.id = md5.new(md5_input).hexdigest()
        
    def get_properties(self):
        properties = {
                      'name' : self.name,
                      'type' : self.type,
                      'required' : self.is_required,
                      'static' : self.is_static,
                     }
        
        if self.parent:
            properties['parent'] = self.parent.id
        
        return self.id, properties
    
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