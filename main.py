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


def list_versions(filename):
    file_tracking_head = get_file_tracking_head(filename)
    for item in file_tracking_head:
        branch = item.get('branch')
        print('Stored versions of ' + item.get('filename'))
        commits = list(repo.iter_commits(branch))
        for c in commits:
            creation_time = datetime.datetime.fromtimestamp(c.committed_date)
            print(f'🔖: "{c.hexsha}" 📄: "{c.message}" ⏱: "{creation_time}" 🙋🏽: "{c.committer.name}"')


def generate_commit_message(num_existing_versions):
    return 'Version ' + (num_existing_versions + 1)


def track_new_file(filename):
    import random
    import string
    # Generate a new random branch name that is not already taken
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
    repo.index.commit(generate_commit_message(0))
    repo.head.reference = master_branch


def get_file_tracking_head(filename):
    db_entry = Query()
    db_search = db.search(db_entry.filename == filename)
    if len(db_search) == 0:
        print(f'No versions of {filename} are currently being tracked by versions')
        return None
    return db_search


def list_all_tracked_files():
    print('Files being tracked by versions')
    all_entries = db.all()
    for item in all_entries:
        print(item.get('filename'))


if __name__ == '__main__':
    command = input("Enter command\t")
    filename = input("Enter filename\t")

    if (command == 'ls'):
        if any([filename == '', filename == None]):
            list_all_tracked_files()
            exit()
        else:
            list_versions(filename)
            exit()

    file_path = os.path.join(pwd, filename)
    file_exists = os.path.exists(file_path)
    if not file_exists:
        print(f'{file_path} doesnt exist')
        exit()

    if(command == 'cm'):
        file_tracking_head = get_file_tracking_head(filename)
        if file_tracking_head == None:
            track_new_file(filename)
        else:
            list_versions(filename)