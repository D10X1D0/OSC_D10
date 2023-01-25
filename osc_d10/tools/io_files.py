import json

from osc_d10.tools.console_colors import bcolors


def print_warning(msg):
    print(f"{bcolors.WARNING} {msg} {bcolors.ENDC}")


def create_default_file(filename, data):
    print_warning(f"Creating default config file:{filename}")
    try:
        json_dump = json.dumps(data, indent=4)
        with open(filename, "w") as f:
            f.write(json_dump)
    except Exception as e:
        print_warning(f"Could not create a default config file for {filename}, error : {e}")


def try_read_json(filename):
    with open(filename) as f:
        data = json.load(f)
        return data


def read_json_file(filename: str, default_value):
    # read a .json file, if it fails creates a default one.
    try:
        data = try_read_json(filename)
        return data
    except OSError as e:
        print_warning("Could not load " + filename)
        create_default_file(filename, default_value)
        data = try_read_json(filename)
        return data
    except Exception as e:
        print(f"Could not load + {filename}")
        print(f"Exception :  {e}")
        return False

