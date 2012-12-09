from boto import *
import sys, os, logging

class ConnectionManager(object): 
    def __init__(self, project_name, config_manager):
        self.project_name = project_name
        self.config_manager = config_manager
        self.connections = {}
        self.setup_provider = {}
        self.setup_provider['aws'] = self.setup_aws
        self.setup_provider['openstack'] = self.setup_openstack
        self.setup_provider['iplant'] = self.setup_iplant

    def spawn_workers(self, provider, num_instances, user_data, size=''):
        if not num_instances:
            return []

        if provider not in self.setup_provider:
            logging.warn("Unable to spawn workers. The provider %s is not recognized." % provider)
            return []

        if provider not in self.connections:
            self.connections[provider] = self.setup_provider[provider]()
        
        if not size:
            (instance, keypair, groups, size) =  self.config_manager.get_provider(provider)
        else:
            (instance, keypair, groups, s1) =  self.config_manager.get_provider(provider)

        conn = self.connections[provider]
        res = conn.run_instances(instance, key_name=keypair,
            security_groups=groups, instance_type=size,
            max_count=num_instances, user_data=user_data)

        if provider == "aws":
            conn.create_tags(map(lambda x: x.id, res.instances), {"Name" : self.project_name})

        return res.instances

    def split_groups(self, groups, delimiter=","):
        return [item.strip() for item in groups.split(delimiter)]
    
    def setup_aws(self):
        logging.info("Configuring AWS connection.")
        user_id = boto.config.get("Credentials", "aws_access_key_id")
        secret_key = boto.config.get("Credentials","aws_secret_access_key")
        connection = connect_ec2(user_id, secret_key)

        instance_id = boto.config.get("Instances", "aws_instance_id")
        keypair = boto.config.get("Instances", "aws_instance_keypair")
        groups = self.split_groups(boto.config.get("Instances", "aws_security_groups"))
        size = boto.config.get("Instances", "aws_instance_size")
 
        if instance_id and keypair and groups and size:
            self.config_manager.register_provider("aws", instance_id,
                keypair, groups, size)
        else:
            logging.error("AWS could not be configured.")
            sys.exit(1)

        return connection

    def setup_iplant(self):
        pass

    def setup_openstack(self):
        logging.info("Configuring Openstack connection.")
        user_id = boto.config.get("Credentials", "openstack_access_key_id")
        secret_key = boto.config.get("Credentials","openstack_secret_access_key")
        connection = connect_ec2(user_id, secret_key)
        connection.host= '149.165.146.50'
        connection.port = 8773
        connection.is_secure = False
        connection.path = "/services/Cloud"
 
        instance_id = boto.config.get("Instances", "openstack_instance_id")
        keypair = boto.config.get("Instances", "openstack_instance_keypair")
        groups = self.split_groups(boto.config.get("Instances", "openstack_security_groups"))
        size = boto.config.get("Instances", "openstack_instance_size")

        if instance_id and keypair and groups and size:
            self.config_manager.register_provider("openstack", instance_id,
                keypair, groups, size)
        else:
            logging.error("Openstack could not be configured.")
            sys.exit(1)

        return connection

