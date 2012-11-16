#!/usr/bin/python

from __future__ import print_function
import git
import re
import datetime
import os
import subprocess
import contextlib
import shutil

@contextlib.contextmanager
def chdir(path):
    old = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(old)

goals = ['thesis.pdf', 'thesis-print.pdf']

snapshot_re = re.compile('snapshot([0-9]+)')

directory = os.path.dirname(__file__)
repo = git.Repo(directory)

print("** Make PDF")
with chdir(directory):
    subprocess.check_call('make ' + ' '.join(goals), shell=True)

print("** Existing snapshots:")
snapshots = []
for t in repo.tags:
    if not snapshot_re.match(str(t)):
        continue

    snapshots.append(t)

    print(t,
        datetime.datetime.fromtimestamp(t.commit.authored_date))

last_number = max(int(snapshot_re.match(str(s)).group(1)) for s in snapshots)
next_name ='snapshot{}'.format(last_number + 1)
print("** Creating {}".format(next_name))

repo.create_tag(next_name)

origin = repo.remotes.origin
origin.push()
