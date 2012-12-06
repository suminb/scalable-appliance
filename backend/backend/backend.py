from work_queue import *
from boto import *
from connectionManager import *
from configurationManager import *
from simpleWorker import *
import sys, logging

class Backend(object):
    def __init__(self, project_name, config="/etc/acic.cfg", port=WORK_QUEUE_DEFAULT_PORT):
        self.project_name = project_name
        self.config_manager = ConfigurationManager()
        self.connection_manager = ConnectionManager(project_name, self.config_manager)
        self.port = port
        self.instances = {}
       
        DEFAULT_CONFIG = "/etc/acic.cfg"
        
        if config:
            self.load_or_die(args.config,
                error=("The configuration file %s could not be opened." % config))
        else:
            self.load_or_die(DEFAULT_CONFIG)

        self.config_manager.set_option("project",
            value=boto.config.get("Backend", "project"))
        self.config_manager.set_option("work_dir",
            value=boto.config.get("Backend", "work_dir"))
        self.config_manager.set_option("output_dir",
            value=boto.config.get("Backend", "output_dir"))
        self.config_manager.set_option("deploy",
            value=boto.config.get("Backend", "deploy"))
        self.config_manager.set_option("startup_script",
            value=boto.config.get("Backend", "startup_script"))
    
    def load_or_die(self, path, error="A configuration file could not be found in the default locations."):
        try:
            boto.config.load_from_path(path)
        except:
            print error
            sys.exit(1)
   
    def start(self):
        try:
            self.queue = WorkQueue(port = self.port, name = self.project_name, catalog = True)
            self.queue.activate_fast_abort(-1)
            logging.info("Started Work Queue master on port %d" % self.port)
        except:
            logging.error("Unable to start Work Queue master.")
            sys.exit(1);

    def stop(self):
        for (id, instance) in self.instances.iteritems():
            instance.terminate()
    
    def update(self):
        print "----Backend Status----"
        print "Tasks Waiting:      %s" % self.queue.stats.tasks_waiting
        print "Tasks Running:      %s" % self.queue.stats.tasks_running 
        print "Tasks Complete:     %s" % self.queue.stats.tasks_complete
        print "Workers Not Ready:  %s" % self.queue.stats.workers_init
        print "Workers Ready:      %s" % self.queue.stats.workers_ready
        print "Workers Busy:       %s\n" % self.queue.stats.workers_busy

        task = self.queue.wait(10)

        if (task):
            logging.info("Task %d: %s completed with return status: %d" % (t.id,
                t.command, t.return_status))

        return task

    def running(self):
        return not self.queue.empty()

    def add_workers(self, provider, num_instances, user_data):
        instances = self.connection_manager.spawn_workers(provider, num_instances, user_data)
        if not instances:
            return

        for instance in instances:
            self.instances[instance.id] = instance
        
    def submit_work(self, worker):
        worker_id = self.queue.submit(worker)

        if worker_id:
            logging.info("Worker %d has been scheduled." % worker_id)
        else:
            logging.error("Worker was unable to be scheduled.")
