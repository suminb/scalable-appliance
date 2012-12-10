from boto import *

class ConfigurationManager(object):
    def __init__(self) :
        self.options = {}
        self.providers = {}
    
    def has_option(self, option):
        return option in self.options
    
    def get_option(self, option):
        if option in self.options:
            return self.options[option]
        else:
            return None
    
    def set_option(self, option, value):
        if value:
            self.options[option] = value
    
    def empty(self):
        return bool(self.providers)

    def has_provider(self, provider):
        return provider in self.providers

    def get_attribute(self, provider, attribute):
        if self.has_provider(provider):
            attrs = self.providers[provider]
        else:
            return None

        if attribute in attrs:
            return attrs[attribute]
        else:
            return None
    
    def get_provider(self, provider):
        if not self.has_provider(provider):
            return None
        
        return self.providers[provider].itervalues()

    def set_attribute(self, provider, attribute, value=""):
        if self.has_provider(provider):
            self.providers[provider][attribute] = value

    def register_provider(self, provider, instance_id, keypair, groups, size):
        if not instance_id or not keypair or not groups or not size: 
            return
        elif self.has_provider(provider):
            return
        else:
            self.providers[provider] = {'instance:' : instance_id,
                'keypair' : keypair, 'groups' : groups,
                'size' : size }

    def remove_provider(self, provider):
        if self.has_provider(provider):
            del self.config[provider]

