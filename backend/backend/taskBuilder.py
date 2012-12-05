from work_queue import * 
import sys, os, logging, tempfile

class TaskBuilder():
    def __init__(self, cmdline, input_dir="", remote_dir="", output_dir="", wildcard="*"):
        self.cmdline = cmdline.strip()
        self.remote_dir = remote_dir
        self.output_dir = output_dir 
        self.input_dir = input_dir
        self.files = []
        self.prehooks = []
        self.posthooks = []
        self.temp_files = []
        self.temp_dir = tempfile.mkdtemp(prefix="backend-")
        self.wildcard = wildcard
        self.cur_id = 0

    def build_task(self, work_file):
        name = os.path.basename(work_file).strip()

        if not work_file:
            logging.warn("no work_file specified.")
            return

        if not self.add_file(work_file, source_dir=self.input_dir):
            logging.warn(name + ": could not add worker.")
            return
        
        try:
            script_name = "worker-" + str(self.cur_id) + ".sh"
            script = os.path.join(self.temp_dir, script_name)
            fp = open(script, 'w+')

            fp.write(self.append_newline("#!/bin/bash"))

            # Generate prehooks
            for cmdstring in self.prehooks:
                prehook_msg = 'echo "running %s"\n' % cmdstring.strip()
                fp.write(prehook_msg)
                fp.write("./%s" % cmdstring)

            # COMMAND
            if os.path.isfile(os.path.abspath(self.cmdline)):
                cmdpath = os.path.abspath(self.cmdline)
                cmdstring = "./%s %s" % (self.cmdline, name)
            else:
                cmdstring = "%s %s" % (self.cmdline, name)

            cmd_status = 'echo "running %s"\n' % name
            fp.write(cmd_status)
            fp.write(self.append_newline(cmdstring))
            
            # Generate posthooks
            for cmdstring in self.posthooks:
                arg_index = cmdstring.find(" ")
                cmd = cmdstring[:arg_index]
                posthook_msg = 'echo "running %s"\n' % cmd.strip()
                fp.write(posthook_msg)
                fp.write("./%s" % cmdstring)
        except Exception as e:
            print str(e)
            logging.warn(script_name + ": task could not be written.")
            return None
        finally:
            self.cur_id = self.cur_id + 1
            self.temp_files.append(script_name)
            logging.info(script_name + " was added.")
            fp.close()

        # Add files to the Task
        worker = Task("/bin/bash %s" % script_name)

        if cmdpath:
            worker.specify_file(cmdpath, cmdstring, type=WORK_QUEUE_INPUT) 

        for (localfile, queue_type, cache) in self.files:
            if self.wildcard in localfile:
                ext_index = name.rfind(".")
                localfile = localfile.replace(self.wildcard, name[:ext_index])

            filename = os.path.basename(localfile)
            remote = os.path.join(self.remote_dir, filename)
            worker.specify_file(localfile, filename,
                type=queue_type, cache=cache)

        worker.specify_file("/bin/bash", "bash", type=WORK_QUEUE_INPUT)
        worker.specify_file(script, script_name, type=WORK_QUEUE_INPUT,
            cache=False)
        
        return worker

    def append_newline(self, string):
        return string + "\n"

    def add_hooks(self, hooks, source_dir="", before=True):
        if not hooks:
            return

        for cmdstring in hooks:
            cmdstring = cmdstring.strip()
            cmd = cmdstring.split()[0]
            
            if self.add_file(cmd, source_dir=source_dir):
                if before:
                    self.prehooks.append(self.append_newline(cmdstring))
                else:
                    self.posthooks.append(self.append_newline(cmdstring))
                logging.info(cmd + ": was successfully added for deployment.") 
            else:
                logging.warn(cmdstring + ": will not be deployed.")
    
    def add_file_group(self, files, source_dir="", remote=False):
        if not files:
            return

        for f in files:
            self.add_file(f, source_dir=source_dir, remote=remote)
            
    def add_file(self, filename, source_dir="", remote=False):
        filename = filename.strip()
        name = os.path.basename(filename)
        dfile = os.path.join(source_dir, name)
        
        found = [os.path.isfile(filename), os.path.isfile(dfile)]
        success = True

        exist = [os.path.basename(fn) == name for (fn, t, c) in self.files]

        if remote and self.wildcard in filename:
            output_name = os.path.join(self.output_dir, filename)
            output_file = (output_name, WORK_QUEUE_OUTPUT, False)
            self.files.append(output_file)
        elif any(exist) or (remote and found):
            logging.warn(name + ": this result file already exists.")
            success = False
        elif not found and remote:
            output_name = os.path.join(self.output_dir, filename)
            output_file = (output_name, filename, WORK_QUEUE_OUTPUT, False)
            self.files.append(output_file)
        elif found[0]:
            input_file = (filename, WORK_QUEUE_INPUT, True)
            self.files.append(input_file)
        elif found[1]:
            input_file = (dfile, WORK_QUEUE_INPUT, True)
            self.files.append(input_file)
        else:
            logging.warn(name + ": does not exist.")
            success = False

        return success
        
    def cleanup(self):
        try:
            for tmpfile in self.temp_files:
                os.path.join(self.temp_dir, tmpfile)
            
            os.rmdir(self.temp_dir)
        except:
            print "%s was not completely removed." % self.temp_dir

if __name__ == "__main__":
    print "Testing TaskBuilder"
    builder = TaskBuilder("maker",
        input_dir="%s/test" % os.getcwd(),
        remote_dir="/home/ubuntu/work/",
        output_dir="/proj_data/results")

    builder.add_file("test.txt", "")
