import os

import git
from git import Repo
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


def newFile(file_path):
    import random
    import string
    branch_already_exists = True
    while branch_already_exists:
        branch_name = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(20))
        db_entry = Query()
        db_search = db.search(db_entry.branch == branch_name)
        branch_already_exists = len(db_search) > 0
    repo.create_head(branch_name)
    db.insert({'filename': file_path, 'branch': branch_name})
    print(f'Created a new git branch called {branch_name} to track {file_path}')
    repo.index.add([file_path])
    repo.index.commit("version 1")


if __name__ == '__main__':
    filename = input("Enter filename\t")
    file_path = os.path.join(pwd, filename)
    file_exists = os.path.exists(file_path)
    if not file_exists:
        print(f'{file_path} doesnt exist')
        exit()
    newFile(file_path)
