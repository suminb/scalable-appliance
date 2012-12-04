from work_queue import * 
import sys, os, logging, tempfile

class TaskBuilder():
    def __init__(self, cmd, args="", input_dir="", remote_dir="", output_dir=""):
        self.cmd = cmd
        self.args = args
        self.remote_dir = remote_dir
        self.output_dir = output_dir 
        self.input_dir = input_dir
        self.files = []
        self.prehooks = []
        self.posthooks = []
        self.temp_files = []
        self.temp_dir = ""

    def get_task(self, worker_id):
        try:

            script_name = "%s%s%s" % ("worker-", str(worker_id), ".sh")

            if not self.temp_dir:
                self.temp_dir = tempfile.mkdtemp(prefix="backend-")
            
            script = open("%s/%s" % (self.temp_dir, script_name), 'w+')
            script.write(self.append_newline("#!/bin/bash"))

            # Generate prehooks
            for cmdstring in self.prehooks:
                script.write("echo running %s" % cmdstring)
                script.write(cmdstring)

            # Command
            cmdlist = [self.cmd]
            cmdlist.extend(self.args) 
            script.write(self.append_newline(' '.join(cmdlist)))
        

            # Generate posthooks
            for cmdstring in self.posthooks:
                script.write("echo running %s" % cmdstring)
                script.write(cmdstring)

        except:
            print "The file %s was unable to be open for writing" % script_name
            sys.exit(1)
        finally:
            self.temp_files.append(script_name)
            script.close()

        # Add files to the Task
        worker = Task("/bin/bash %s" % script_name)
        
        for (localfile, queue_type, cache) in self.files:
            filename = os.path.basename(localfile)
            remote = "%s/%s" % (self.remote_dir, filename)
            worker.specify_file(localfile, filename, type=queue_type, cache=cache)
        
        worker.specify_file("/bin/bash", "bash", WORK_QUEUE_INPUT, cache=True)
        worker.specify_file("%s/%s" % (self.temp_dir, script_name),
            script_name, WORK_QUEUE_INPUT, cache=True)

        # Clear for new Task
        self.files = []
        self.prehooks = []
        self.posthooks = []
        return worker

    def append_newline(self, string):
        return string + "\n"

    def add_prehook(self, cmd, script="", args=""):
        if not cmd:
            logging.warn("Please specify a command.")
            return
    
        cmdlist = [cmd, script]
        
        if isinstance(args, list):
            cmdlist.extend(args)
        else:
            cmdlist.append(args)

        cmdline = ' '.join(cmdlist)
        self.prehooks.append(self.append_newline(cmdline))


    def add_posthook(self, cmd, script="", args=""):
        if not cmd:
            logging.warn("Please specify a command.")
            return
    
        cmdlist = [cmd, script]
        
        if isinstance(args, list):
            cmdlist.extend(args)
        else:
            cmdlist.append(args)

        cmdline = ' '.join(cmdlist)
        self.posthooks.append(self.append_newline(cmdline))

    def add_input(self, filename, cache=False):
        filename = filename.strip()
        name = os.path.basename(filename)
        input_file = "%s/%s" % (self.input_dir, name)

        if os.path.isfile(filename): 
            self.files.append((filename, WORK_QUEUE_INPUT, cache))
        elif os.path.isfile(input_file):
            self.files.append((input_file, WORK_QUEUE_INPUT, cache))
        else:
            logging.warn("The file %s does not exist." % name)

    def add_output(self, filename, cache=False):
        filename = filename.strip()
        output_file = "%s/%s" % (self.output_dir, os.path.basename(filename))
        
        if os.path.isfile(filename):
            self.files.append((filename, WORK_QUEUE_OUTPUT, cache))
            logging.warn("The output file %s specified currently exists and will be overwritten" % filename)
        if os.path.isfile(output_file):
            self.files.append((output_file, WORK_QUEUE_OUTPUT, cache))
            logging.warn("The output file %s specified currently exists and will be overwritten" % output_file)
        else:
            self.files.append((output_file, WORK_QUEUE_OUTPUT, cache))
        
    def cleanup(self):
        try:
            for tmpfile in self.temp_files:
                os.remove("%s/%s" % (self.temp_dir, tmpfile))
            
            os.rmdir(self.temp_dir)
        except:
            print "%s was not completely removed." % self.temp_dir

if __name__ == "__main__":
    print "TEST: Generating setup script"

    builder = TaskBuilder("maker",
        input_dir="%s/test" % os.getcwd(),
        remote_dir="/home/ubuntu/work/",
        output_dir="/proj_data/results")

    builder.add_prehook("maker", args=["-CTL"])

    builder.add_prehook("python", script="setoption.py",
        args=["file1.txt me two three"])

    builder.add_prehook("python", script="setoption.py",
        args=["file2.txt me two three"])

    builder.add_input("file1.txt")
    builder.add_input("file2.txt")
    builder.add_output("file3.txt")
    builder.add_input("file4.txt", cache=True)
    builder.add_input("file5.txt", cache=True)

    builder.add_posthook("tar xzvf file.tar.gz file1.txt file2.txt")
    builder.get_task(1)

    builder.cleanup()
