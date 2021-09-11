import datetime
import os

import git
from git import Repo, Head
from tinydb import TinyDB, Query

pwd = '/Users/tssingal/Documents/versions-testing'
# os.getcwd()
db = TinyDB(pwd + '/.versions_db.json')


def init_repo():
    r = Repo.init(pwd)
    print(f"Created new git repository at {pwd}")
    # This function just creates an empty file ...
    startup_test = os.path.join(pwd, '.versions_init_object')
    open(startup_test, 'wb').close()
    r.index.add([startup_test])
    r.index.commit("Started using versions!")
    os.remove(startup_test)
    return r


try:
    repo = Repo(pwd)
except (git.exc.NoSuchPathError) as e:
    print("No existing git repository found")
    repo = init_repo()
except (git.exc.InvalidGitRepositoryError) as e:
    print("No valid git repository found")
    repo = init_repo()

master_branch = Head(repo, 'refs/heads/master')


def listVersions(filename):
    db_entry = Query()
    db_search = db.search(db_entry.filename == filename)
    if len(db_search) == 0:
        print(f'No versions of {filename} are currently being tracked by versions')
    for item in db_search:
        branch = item.get('branch')
        print('Stored versions of ' + item.get('filename'))
        commits = list(repo.iter_commits(branch))
        for commit in commits:
            creation_time = datetime.datetime.fromtimestamp(commit.committed_date)
            print(f'V: "{commit.message}" D: "{creation_time}" A: "{commit.committer.name}"')


def newFile(filename):
    import random
    import string
    branch_already_exists = True
    while branch_already_exists:
        branch_name = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(20))
        db_entry = Query()
        db_search = db.search(db_entry.branch == branch_name)
        branch_already_exists = len(db_search) > 0
    # Change the head reference to the new branch
    repo.head.reference = Head(repo, 'refs/heads/' + branch_name)
    db.insert({'filename': filename, 'branch': branch_name})
    print(f'Created a new git branch called {branch_name} to track {filename}')
    repo.index.add([filename])
    repo.index.commit("version 1")
    repo.head.reference = master_branch


if __name__ == '__main__':
    filename = input("Enter filename\t")
    file_path = os.path.join(pwd, filename)
    file_exists = os.path.exists(file_path)
    if not file_exists:
        print(f'{file_path} doesnt exist')
        exit()
    newFile(filename)
    listVersions(filename)
