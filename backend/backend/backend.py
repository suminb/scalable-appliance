from work_queue import *
from boto import *
from connectionManager import *
from configurationManager import *
from taskBuilder import *
import sys, logging

class Backend(object):
    def __init__(self, project_name, cmd, config):
        self.project_name = project_name
        self.config_manager = config
        self.connection_manager = ConnectionManager(project_name, self.config_manager)
        self.instances = {}
        self.running = False
        self.work = []
        self.scheduled = []

        configfile = self.config_manager.get_option("config")
        msg  = configfile + ": configuration file could not be opened."
        self.load_or_die(configfile, error=msg)

        self.config_manager.set_option("work_dir",
            value=boto.config.get("Backend", "work_dir"))
        self.config_manager.set_option("output_dir",
            value=boto.config.get("Backend", "output_dir"))
        self.config_manager.set_option("deploy",
            value=boto.config.get("Backend", "deploy"))
        self.config_manager.set_option("startup_script",
            value=boto.config.get("Backend", "startup_script"))
        
        if not self.config_manager.has_option("port"):
            if boto.config.has_option("Backend", "port"): 
                self.config_manager.set_option("port",
                    boto.config.get("Backend", "port"))
            else:
                self.config_manager.set_option("port", WORK_QUEUE_DEFAULT_PORT)
        
        self.builder = TaskBuilder(cmd,
            input_dir= self.config_manager.get_option("work_dir"),
            remote_dir="",
            output_dir=self.config_manager.get_option("output_dir"))

    def load_or_die(self, path, error="A configuration file could not be found."):
        try:
            boto.config.load_from_path(path)
        except:
            print error
            sys.exit(1)
   
    def start(self):
        self.running = True
        p = int(self.config_manager.get_option("port"))
        
        try:
            self.queue = WorkQueue(port = p, name = self.project_name, catalog = True)
            logging.info("Started Work Queue master on port %d" % p)
        except:
            logging.error("Unable to start Work Queue master. Try another port.")
            sys.exit(1);

        for files in self.work:
            self.submit_work(files)

        for (provider, num_instance, user_data) in self.scheduled:
            self.add_workers(provider, num_instances, user_data)

        del self.work
        del self.scheduled

    def stop(self):
        self.running = False
        for (id, instance) in self.instances.iteritems():
            instance.terminate()

        self.work = []
        self.scheduled = []
        self.builder.cleanup()
    
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
            info = (task.id, task.command, task.return_status)
            logging.info("Task %d: %s completed with return status %d." % info)

        return task

    def done(self):
        return self.queue.empty()

    def running(self):
        return self.running

    def add_workers(self, provider, num_instances, user_data=""):
        if not(running):
            self.schedule.append((provider, num_instances, user_data))
            return

        if user_data or not self.startup:
            instances = self.connection_manager.spawn_workers(provider,
                num_instances, user_data)
        else:
            instances = self.connection_manager.spawn_workers(provider,
                num_instances, self.startup)

        if not instances:
            return

        for instance in instances:
            self.instances[instance.id] = instance
        
    def submit_work(self, files):
        if not self.running:
            self.work.append(files)
            return

        if not isinstance(files, list):
            files = [files]

        for work_file in files:
            task = self.builder.build_task(work_file)

            if not task:
                logging.error(work_file + ": was not scheduled.")
                continue
            
            worker_id = self.queue.submit(task)

            if worker_id:
                logging.info("Worker %d has been scheduled." % worker_id)
            else:
                logging.error("Worker was unable to be scheduled.")

    def deploy_files(self, deploy_file):
        try:
                fp = open(deploy_file)
                full_path = os.path.abspath(deploy_file)
                index = full_path.find(os.path.basename(full_path))
                deploy_path = str(full_path[:index])
                deploy_path.strip()
                lines = fp.readlines()
                fp.close()
        except:
            print "The deploy file %s could not be opened." % deploy_file
            return

        if not lines:
            print deploy_file + " was an empty file."
            return

        scripts = filter(lambda x : x.startswith("startup:"), lines)
        prehooks = filter(lambda x : x.startswith("before:"), lines)
        posthooks = filter(lambda x : x.startswith("after:"), lines)
        data = filter(lambda x : x.startswith("data:"), lines)
        results = filter(lambda x : x.startswith("result:"), lines)
        
        scripts = map(lambda x : x[8:], scripts)
        prehooks= map(lambda x : x[7:], prehooks)
        posthooks = map(lambda x : x[6:], posthooks)
        data = map(lambda x : x[5:], data)
        results = map(lambda x : x[7:], results)
        
        if len(scripts) == 1:
            try:
                script_file = scripts[0].strip()
                if os.path.isfile(script_file):
                    fp = open(os.path.abs.path(script_file))
                    config = fp.read()
                else:
                    fp = open(os.path.join(deploy_path, script_file))
                    config = fp.read()

                config = config.replace("%PROJECT%", self.project_name)
                self.startup_script = config
            except:
                print "The startup script %s could not be opened." % script_file
            finally:
                fp.close()
        else:
            print "Only 1 startup file can be specified."

        self.builder.add_hooks(prehooks, source_dir=deploy_path)
        self.builder.add_hooks(posthooks, source_dir=deploy_path,
            before=False)
        self.builder.add_file_group(data, source_dir=deploy_path)
        self.builder.add_file_group(results, source_dir=deploy_path,
            remote=True)
        logging.info("Finished adding deploy file.")

