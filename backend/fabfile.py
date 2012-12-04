from fabric.api import run, env

#
# Using `fab` command:
# $ fab -H pistachio memory_usage
#

def memory_usage():
	run("free")

def disk_usage():
	run("df -h")


class FabricSupport:
    def __init__ (self):
        pass

    def run(self, host, port, command):
        env.host_string = "%s:%s" % (host, port)
        run(command)


if __name__ == "__main__":
	fab = FabricSupport()
	fab.run("pistachio", 22, "uname -a")