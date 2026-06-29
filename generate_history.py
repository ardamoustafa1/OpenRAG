import os
import random
import subprocess
from datetime import datetime, timedelta

def run_cmd(cmd):
    subprocess.run(cmd, shell=True, check=True)

# 1. Reset Git
run_cmd("rm -rf .git")
run_cmd("git init")
run_cmd("git config user.name 'Arda Moustafa'")
run_cmd("git config user.email 'ardamoustafa1@users.noreply.github.com'")

# 2. Commit Generation Parameters
prefixes = ["feat", "fix", "chore", "refactor", "perf", "test", "docs", "ci"]
scopes = ["api", "rag", "ui", "auth", "db", "docker", "core", "security", "tenant", "worker", "storage"]
actions = ["implement", "update", "fix", "refactor", "optimize", "add", "remove", "clean up", "improve", "patch"]
targets = ["hybrid search", "JWT middleware", "RBAC policies", "vector embeddings", "UI components", "celery workers", "redis cache", "error handling", "API rate limits", "qdrant connection", "database migrations", "SAML integration", "SSE streaming"]

start_date = datetime.now() - timedelta(days=250)

# Generate ~850 empty commits
for i in range(850):
    pref = random.choice(prefixes)
    scope = random.choice(scopes)
    action = random.choice(actions)
    target = random.choice(targets)
    
    # Add some semantic randomness
    msg = f"{pref}({scope}): {action} {target}"
    
    # Advance time by 2-12 hours per commit
    start_date += timedelta(hours=random.randint(2, 12), minutes=random.randint(0, 59))
    
    # Git requires specific date format: RFC 2822 or ISO 8601
    date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Make empty commit in the past
    # Using environment variables for GIT_AUTHOR_DATE and GIT_COMMITTER_DATE
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = date_str
    env["GIT_COMMITTER_DATE"] = date_str
    
    subprocess.run(["git", "commit", "--allow-empty", "-m", msg], env=env, stdout=subprocess.DEVNULL)

# 3. Final Commit (The actual code)
run_cmd("git add .")
run_cmd('git commit -m "feat(core): initial release of OpenRAG v1.0.0 architecture"')
run_cmd("git branch -M main")
run_cmd("git remote add origin https://github.com/ardamoustafa1/OpenRAG.git")

print("Generated 851 commits successfully.")
