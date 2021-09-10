import git
import os
from tinydb import TinyDB, Query

pwd = '/Users/tssingal/Documents/versions-testing'
#os.getcwd()
db = TinyDB(pwd + '/db.json')
repo = git.Repo(pwd)

def newFile(filename):
    import random
    import string
    branch_already_exists = True
    while branch_already_exists:
        branch_name = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(20))
        print(branch_name)
        Entry = Query()
        db_search = db.search(Entry.branch == branch_name)
        branch_already_exists = len(db_search) > 0
    repo.create_head(branch_name)
    print(f'Created a new git branch called {branch_name} to track {filename}')

if __name__ == '__main__':
    filename = input("Enter filename\t")
    print(f"You entered {filename}!")
    branches = repo.branches
    print(branches)
    newFile("someFileName")
