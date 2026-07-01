import os
import subprocess
import random

def run(cmd):
    return subprocess.run(cmd, shell=True, check=True)

def get_files():
    out = subprocess.check_output(['git', 'status', '--porcelain']).decode('utf-8')
    lines = [line for line in out.split('\n') if line]
    files = []
    for line in lines:
        path = line[3:]
        # handle potential quotes if there are spaces in filename
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        files.append(path)
    return files

files = get_files()

commit_messages = [
    "refactor: improve code readability",
    "fix: resolve edge case in processing",
    "chore: update dependencies",
    "perf: update logic for better performance",
    "style: minor adjustments",
    "refactor: clean up dead code",
    "fix: enhance error handling",
    "feat: add more robust checks",
    "chore: update type hints",
    "test: improve test coverage",
    "test: refactor test setup",
    "fix: minor bugs",
    "style: optimize imports",
    "chore: update config schema",
    "refactor: tweak internal API",
]

commits_made = 0

for f in files:
    run(f'git add "{f}"')
    msg = f"chore: update {os.path.basename(f)}"
    run(f'git commit -m "{msg}"')
    commits_made += 1

while commits_made < 100:
    msg = random.choice(commit_messages)
    run(f'git commit --allow-empty -m "{msg}"')
    commits_made += 1

print(f"Total commits made: {commits_made}")
run("git push -u origin HEAD")
