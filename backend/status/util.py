__author__ = "Sumin Byeon <suminb@gmail.com>"

import re
import json
import subprocess

def memory_usage():
	stdout = subprocess.check_output(("free", "-k"))

	# This may break in some systems
	rows = stdout.strip().split("\n")
	mem_cols = rows[1].split()
	swap_cols = rows[3].split()

	return {"memory":{"capacity":mem_cols[1], "used":mem_cols[2]},
		    "swap":{"capacity":swap_cols[1], "used":swap_cols[2]}}


def disk_usage():
	data = []

	# k: --block-size=1K
	# P: use the POSIX output format
	stdout = subprocess.check_output(("df", "-kP"))

	rows = stdout.strip().split("\n")
	header = rows[0]

	for row in rows[1:]:
		cols = row.split()

		d = {"capacity":cols[3], "used":cols[2], "mountpoint":cols[5]}
		data.append(d)

	return data


if __name__ == "__main__":
	print memory_usage()