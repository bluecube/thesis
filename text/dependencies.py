#!/usr/bin/python

import re
import argparse
import os.path

def force_prefix_build_path(path):
    return os.path.join(args.build_directory, path)

def prefix_build_path(path):
    if exists(path):
        return path
    else:
        return force_prefix_build_path(path)

def exists(path):
    try:
        with open(path, 'r'):
            pass
    except IOError:
        return False
    else:
        return True

def match_file(command, line):
    regexp = re.escape('\\' + command) + r'(?:\[[^\]]*\])*\{([^}]*)\}'
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

def add_to_deps(path, origin = None):
    global current_file
    global current_line

    if origin is None:
        origin = "{}:{}".format(current_file, current_line)
    dependencies.setdefault(path, []).append(origin)

parser = argparse.ArgumentParser(description="""Find dependencies of a tex file.

Read input files line by line and look for "includegraphics", "addbibresource",
"input" and "usepackage" commands. If the referenced file exists, it is added
as a dependency, if it does not, then with "usepackage" it is skipped and
with all other commands it is first prefixed with build path and added to
dependencies.
If they exist, files found with "input" and "usepackage" are also added to
the list of source files and scanned for dependencies themselves.
One additional rule is, that input'd file in build directory will not be read
as an input even if it exists.""")
parser.add_argument('files', nargs='+')
parser.add_argument('--build-directory',
    help='build directory to prefix to path to generated files.')
args = parser.parse_args()

files_to_check = args.files
dependencies = {f: ["argument"] for f in args.files}

for line in lines():
    line = re.sub(r'(^|[^\\])%.*$', '$1', line)

    graphics = match_file('includegraphics', line)
    if graphics:
        graphics = prefix_build_path(graphics)
        add_to_deps(graphics)

    listing = match_file('lstinputlisting', line)
    if listing:
        listing = prefix_build_path(listing)
        add_to_deps(listing)

    bibresource = match_file('addbibresource', line)
    if bibresource:
        bibresource = prefix_build_path(bibresource)
        add_to_deps(bibresource)

    texfile = match_file('input', line)
    if texfile:
        orig_texfile = texfile
        texfile = prefix_build_path(texfile)
        if texfile not in dependencies:
            add_to_deps(texfile)
            if orig_texfile == texfile: # Generated tex files are not processed
                files_to_check.append(texfile)

    package = match_file('usepackage', line)
    if package:
        package = package + ".sty"
        if exists(package):
            add_to_deps(package)
            files_to_check.append(package)

print(' \\\n'.join(sorted(dependencies.keys())))
for filename, sources in sorted(dependencies.items()):
    print("# " + filename + ": " + " ".join(sources))
