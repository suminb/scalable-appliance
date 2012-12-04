import argparse

def set_option(filename, option, value=""):
	with open(filename, "r+") as fp:
		lines = fp.readlines()
		fp.seek(0)

		for line in lines:
			split_line = line.split("=")
			if split_line[0] == option:
				split_line[1] = value
				split_line.insert(1, "=")
				line = "".join(split_line[0:3]) + "\n"

			fp.write(line)	

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("maker_file")
	parser.add_argument("option")
	parser.add_argument("value")
	args = parser.parse_args()

	set_option(args.maker_file, args.option, args.value)
