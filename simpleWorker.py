from work_queue import *

class SimpleWorker(Task):
    def __init__(self, val):
        output = "simple.txt-%s" % val
        super(SimpleWorker, self).__init__('/bin/hostname > %s && /bin/sleep 20' % output)
        self.specify_file("/bin/sleep", "sleep", WORK_QUEUE_INPUT, cache=True)
        self.specify_file("/bin/hostname", "hostname", WORK_QUEUE_INPUT, cache=True)
        self.specify_file(output, output, WORK_QUEUE_OUTPUT, cache=False)
