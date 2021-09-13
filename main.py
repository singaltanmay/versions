import argparse
import datetime
import os
import random
import string

import git
from git import Repo, Head
from tinydb import TinyDB, Query

pwd = '/Users/tssingal/Documents/versions-testing'
# os.getcwd()
app_path = os.path.join(pwd, '.versions')

if not os.path.exists(app_path):
    os.mkdir(app_path)
db = TinyDB(os.path.join(app_path, 'versions_db.json'))


def init_repo():
    r = Repo.init(pwd)
    print(f"Created new git repository at {pwd}")
    # This function just creates an empty file ...
    startup_test = os.path.join(app_path, 'versions_init_object')
    with open(startup_test, 'w') as f:
        f.write(f'Started using versions on {datetime.datetime.now()}')
        f.close()
    r.index.add([startup_test])
    r.index.commit("Started using versions!")
    infoexcludepath = os.path.join(pwd, os.path.join('.git', os.path.join('info', 'exclude')))
    with open(infoexcludepath, 'a') as f:
        f.write(app_path)
        f.close()
    return r


try:
    repo = Repo(pwd)
except git.exc.NoSuchPathError as e:
    print("No existing git repository found")
    repo = init_repo()
except git.exc.InvalidGitRepositoryError as e:
    print("No valid git repository found")
    repo = init_repo()

master_branch = Head(repo, 'refs/heads/master')


def get_file_versions(filename, do_print: False):
    commits_list = []
    file_tracking_head = get_file_tracking_head(filename)
    for item in file_tracking_head:
        branch = item.get('branch')
        print('Stored versions of ' + item.get('filename'))
        commits = list(repo.iter_commits(branch))
        commits_list.append(commits)
        if do_print:
            print_file_versions(commits)
    return commits_list


def print_file_versions(commits):
    for c in commits:
        creation_time = datetime.datetime.fromtimestamp(c.committed_date)
        print(f'🔖: "{c.hexsha}" 📄: "{c.message}" ⏱: "{creation_time}" 🙋: "{c.committer.name}"')


def generate_commit_message(num_existing_versions):
    return 'Version ' + str(num_existing_versions + 1)


def track_new_file(filename):
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
    print("Committed first version")


def commit_new_version(filename):
    tracking_head = get_file_tracking_head(filename)
    if tracking_head is None:
        print("ERROR: Cannot commit new versions of untracked files!")
        return None
    branch_name = tracking_head[0].get('branch')
    repo.head.reference = Head(repo, 'refs/heads/' + branch_name)
    repo.index.add([os.path.join(pwd, filename)])
    commits = list(repo.iter_commits(branch_name))
    repo.index.commit(generate_commit_message(len(commits)))
    repo.head.reference = master_branch
    # in case file disappears -> print(f'git merge {branch_name} --allow-unrelated-histories --squash')
    print(f"Stored new version of {filename}")


def get_file_tracking_head(filename):
    db_entry = Query()
    db_search = db.search(db_entry.filename == filename)
    if len(db_search) == 0:
        print(f'No versions of {filename} are currently being tracked by versions.')
        return None
    return db_search


def list_all_tracked_files():
    print('Files being tracked by versions:')
    all_entries = db.all()
    for item in all_entries:
        print(item.get('filename'))


def restore_file_to_version(filename, commit):
    repo.git.checkout(commit.hexsha, filename)
    print(f'{filename} successfully restored to version {hexsha}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='versions',
                                     description="Track the various versions of your files using a simple CLI")
    parser.add_argument("cmd", help="The command that you want to run", type=str, nargs='*')
    parser.add_argument("-f", "--file", help="The file you want to run the command on", dest="filename", type=str)
    parser.add_argument("-t", "--tag", help="The tag value of a particular version of the file", dest="hexsha",
                        type=str)
    args = parser.parse_args()

    cmd = args.cmd[0]
    # TODO run commands for multiple files
    all_filenames = args.cmd[1::]
    filename = args.filename or all_filenames[0]

    if cmd is None:
        parser.parse_args(['--help'])

    if cmd == 'ls' or cmd == "list":
        if any([filename == '', filename is None]):
            list_all_tracked_files()
            exit(0)
        else:
            get_file_versions(filename, True)
            exit(0)

    if (filename is None):
        print('No file specified. Use the --file flag to input a file. Run "versions --help" for more info.')
        exit()


    if cmd == 'rs' or cmd == 'restore':
        file_tracking_head = get_file_tracking_head(filename)
        if file_tracking_head is None:
            print("ERROR: Cannot restore. File is not being tracked by versions.")
            exit(1)
        version_head = None
        hexsha = args.hexsha
        if hexsha is None:
            print(f'Tag value is required for versions to restore your file.\n'
                  f'Run "versions ls --file {filename}" to find a list of all the stored versions of your file.')
            exit(1)
        # Look for commits for the file with the user provided hexsha value
        for item in file_tracking_head:
            branch = item.get('branch')
            commits = list(repo.iter_commits(branch))
            version_head = list(filter(lambda c: c.hexsha == hexsha, commits))
        if version_head is None or len(version_head) == 0:
            print(f"No version of {filename} found for the tag {hexsha}")
            exit(1)
        restore_file_to_version(filename, version_head[0])


    file_path = os.path.join(pwd, filename)
    file_exists = os.path.exists(file_path)
    if not file_exists:
        print(f'{file_path} doesnt exist')
        exit(1)

    if cmd == 'commit' or cmd == 'cm':
        file_tracking_head = get_file_tracking_head(filename)
        if file_tracking_head is None:
            track_new_file(filename)
        else:
            commit_new_version(filename)
