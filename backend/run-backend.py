from backend import * 
import argparse, logging, sys, os, ConfigParser

def get_arguments():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [options] project command",
        description="Distributes work to various cloud providers.")

    parser.add_argument("project",
        help="name of the project the backend is running.")

    parser.add_argument("command",
        help="command to be executed for each file.")
   
    # General
    parser.add_argument("-w", "--workdir", metavar="",
        help="directory where work will be found")

    parser.add_argument("-r", "--results", metavar="",
        help="directory where results will be stored.")

    parser.add_argument("-c", "--config", metavar="",
        help="configuration file used used by the backend")
    
    parser.add_argument("-d", "--deploy", metavar="",
        help="list of files to be sent to all instances.")

    parser.add_argument("-f", "--file", metavar="", dest="script",
        help="script executed on instance after starting up")
    
    parser.add_argument("--filter", metavar="",
        help="select only files with the following extensions")

    parser.add_argument("-s", "--size", metavar="",
        help="size of the workers to be used")
    
    parser.add_argument("--simulate", action="store_true",
        help="simulates the backend without any instances.")
    
    # AWS
    parser.add_argument("-a", "--aws", dest="aws", metavar="",
        help="number of AWS instances to use", type=int)

    # Openstack
    parser.add_argument("-o", "--openstack", dest="openstack", metavar="",
        help="number of Openstack instances to use", type=int)

    # Iplant
    parser.add_argument("-i", "--iplant", dest="openstack", metavar="",
        help="number of IPlant instances to use", type=int)

    return parser.parse_args()


def configure_settings(args, config):
    if args.deploy and os.path.isfile(args.deploy):
        config.set_option("deploy", args.deploy)
    
    if not args.aws and not args.openstack:
        print "Please specify the number of instances to be used."
        sys.exit(1)
    else:
        config.set_option("num_instances",
            dict(aws=args.aws, openstack=args.openstack))

    if args.script and os.path.isfile(args.script):
        config.set_option("startup_script", args.script)

    if args.workdir and os.path.isdir(args.workdir):
        config.set_option("work_dir", args.workdir)
    
    if args.results and os.path.isdir(args.results):
        config.set_option("output_dir", args.results)

if __name__ == "__main__":
    args = get_arguments() 
    
    if args.config:
        backend = backend.Backend(args.project, args.command, args.config)
    else:
        backend = backend.Backend(args.project, args.command, "/etc/acic.cfg")

    config = backend.config_manager
    configure_settings(args, config)
    
    if config.has_option("startup_script"):
        startup_script = config.get_option("startup_script")
        try:
            script = open(startup_script).read()
        except:
            print "The startup script %s could not be opened." % startup_script
            sys.exit(1) 
    else:
        script = ""

    if config.has_option("deploy"):
        print "Adding deploy files"
        backend.deploy_files(config.get_option("deploy"))
    
    print "Scheduling work"
    if config.has_option("work_dir"):
        path = config.get_option("work_dir")
        tmp = os.listdir(path)
        
        if args.filter:
            filters = args.filter.split()
        else:
            filters = []

        if filters:
            f = [filter(lambda x: x.endswith(f), tmp) for f in filters]
            fl = []
            map(lambda x: fl.extend(x), f)
        else:
            fl = tmp
        
        files = filter(os.path.isfile, map(lambda x : os.path.join(path, x), fl))

        if not files:
            print "No files where found."
            sys.exit(0)

        for f in files:
            logging.info(f + " was found.")

        backend.submit_work(files)
        # TODO add a watcher


    if args.simulate:
        print "Simulated no instances will be running."
    else:
        print "Starting instances"
        workers = config.get_option('num_instances')
        for (provider, num_instances) in workers.iteritems():
            backend.add_workers(provider, num_instances, script)
    
    backend.start() 

    print "Work is being started"
    while not backend.done():
        t = backend.update()
        if t:
            props = (t.id, t.return_status)
            logging.info("Task %s: completed with return status %d" % props)

    backend.stop()
