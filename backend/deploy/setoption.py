import argparse

def set_option(filename, option, value=""):
    with open(filename, "r+") as fp:
        lines = fp.readlines()
        fp.seek(0)
        fp.truncate()

        cleaned = [x for (x,y,z) in map(lambda x: x.partition("#"), lines)]

        for line in cleaned:
            split_line = line.split("=")
            if not line.endswith("\n"):
                line = line + "\n"

            if split_line[0] == option:
                split_line[1] = value
                split_line.insert(1, "=")
                if split_line[2].endswith("\n"):
                    fp.write("".join(split_line[0:3]) + "\n")
                else: 
                    fp.write("".join(split_line[0:3]) + "\n")
            elif len(split_line) > 1 or split_line[0] == "\n": 
                fp.write(line)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("maker_file")
	parser.add_argument("option")
	parser.add_argument("value")
	args = parser.parse_args()

	set_option(args.maker_file, args.option, args.value)
