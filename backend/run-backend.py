from backend import *
from simpleWorker import *

import argparse, sys, ConfigParser, boto

def get_arguments():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [options] project",
        description="Distributes work to various cloud providers.")

    parser.add_argument("project",
        help="name of the project to be run")

    # General
    parser.add_argument("-w", "--workdir", metavar="",
        help="directory where work will be found")

    parser.add_argument("-r", "--results", metavar="",
        help="directory where results will be stored.")

    parser.add_argument("-c", "--config", metavar="",
        help="configuration file used to run instances")
    
    parser.add_argument("-d", "--deploy", metavar="",
        help="list of files to be sent to all instances.")

    parser.add_argument("-f", "--file", metavar="", dest="script",
        help="script executed on instance after starting up")

    parser.add_argument("-s", "--size", metavar="",
        help="size of the workers to be used")
  
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

    backend = backend.Backend(args.project, args.config)
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

    backend.start() 
    
    print "Starting instances"
    workers = config.get_option('num_instances')
    #for (provider, num_instances) in workers.iteritems():
    #    backend.add_workers(provider, num_instances, script)
    
    evidence_files = {'alttest' : "jap_glab_brachy.cdna.fa",
        'protein' : "jap_glab_brachy.pep.fa",
        'rmlib' : "PReDa_121015_short.fasta",
        'repeat_protein' : "TE_protein_db_121015_short_header.fasta",
        'snaphmm' : "O.sativa.hmm" } 

    builder = taskBuilder.TaskBuilder("maker",
        input_dir= config.get_option("work_dir"),
        remote_dir="",
        output_dir=config.get_option("output_dir"))
    
    option_file = "maker_opts.ctl"
    ext = ".fasta"
    deploy_files = []
    
    try:
        if config.has_option("deploy"):
            deploy_file = config.get_option("deploy")
            fp = open(deploy_file)
        else:
            logging.info("No additional files will be deployed to the server.")
   
        if fp:
            deploy_files = fp.readlines()
            full_path = os.path.abspath(deploy_file)
            index = full_path.find(os.path.basename(full_path))
            deploy_path = str(full_path[:index])
            deploy_path.strip()
            fp.close()
    except:
        print "The deploy file %s could not be opened." % deploy_file
        sys.exit(1)
    

    for (idx, filename) in enumerate(os.listdir(builder.input_dir)):
        
        builder.add_input(filename)
        builder.add_prehook("maker", args="-CTL")
        builder.add_prehook("python", script="set_options.py",
            args=[option_file, "genome", filename])
        
        for f in deploy_files:
            builder.add_input(deploy_path + f, cache=True)
       
        full_name = os.path.basename(filename)
        output_dir ="%s.maker.output" % full_name[:full_name.find(ext)]
        output_file = "%s.tar.gz" % output_dir
        
        for (option, filename) in evidence_files.iteritems():
            args = [option_file, option, filename]
            builder.add_prehook("python", script="set_options.py", args=args)
        
        builder.add_posthook("tar",
            args=["cvfz", output_file, output_dir])

        builder.add_posthook("sleep", args="20")

        builder.add_output(output_file)
        task = builder.get_task(idx) 
        backend.submit_work(task)

    print "Waiting on work to finish"
    while backend.running():
        t = backend.update()
        if t:
            print "Task %d: %s completed with return status: %d" % (t.id, t.command, t.return_status)


    builder.cleanup()
    backend.stop()
