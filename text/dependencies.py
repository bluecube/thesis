#!/usr/bin/python

import re
import argparse
import os.path

def prefix_build_path(path):
    if exists(path):
        return path
    else:
        return os.path.join(args.build_directory, path)

def exists(path):
    try:
        with open(path, 'r'):
            pass
    except IOError:
        return False
    else:
        return True

def match_file(regexp, line):
    match = re.findall(regexp, line)
    if len(match) == 0:
        return False
    elif len(match) > 1:
        raise Exception("More than one match for " + regexp)
    else:
        return match[0]

def lines():
    global current_file
    global current_line
    while len(files_to_check):
        current_file = files_to_check.pop()
        current_line = 1
        try:
            with open(current_file, 'r') as f:
                for line in f:
                    yield line
                    current_line += 1
        except IOError:
            pass

def add_to_deps(path):
    global current_file
    global current_line
    dependencies.setdefault(path, []).append(
        "{}:{}".format(current_file, current_line))

parser = argparse.ArgumentParser(description='Find dependencies of a tex file.')
parser.add_argument('files', nargs='+')
parser.add_argument('--build-directory',
    help='build directory to prefix to path to generated files.')
args = parser.parse_args()

files_to_check = args.files
dependencies = {f: ["argument"] for f in args.files}

for line in lines():
    if re.match(r'^\s*%', line):
        continue

    graphics = match_file(r'\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}', line)
    if graphics:
        graphics = prefix_build_path(graphics)
        add_to_deps(graphics)

    bibresource = match_file(r'\addbibresource\{([^}]*)\}', line)
    if bibresource:
        bibresource = prefix_build_path(bibresource)
        add_to_deps(bibresource)

    texfile = match_file(r'\input\{([^}]*)\}', line)
    if texfile:
        texfile = prefix_build_path(texfile)
        if texfile not in dependencies:
            add_to_deps(texfile)
            files_to_check.append(texfile)

    package = match_file(r'\usepackage\{([^}]*)\}', line)
    if package and exists(package):
        add_to_deps(package)
        files_to_check.append(package)

print(' \\\n'.join(sorted(dependencies.keys())))
for k, v in sorted(dependencies.items()):
    print("# " + k + ": " + " ".join(v))
