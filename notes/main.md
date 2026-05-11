# using uv

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```
➜ curl -LsSf https://astral.sh/uv/install.sh | sh
downloading uv 0.11.13 x86_64-unknown-linux-gnu
installing to /home/simha/.local/bin
  uv
  uvx
everything's installed!
➜ 
```

# init uv inside a project

```
cd fastapi_learning
uv init .
```

```
➜  2026_05May_11Mon_fastapi_learning uv init .
Initialized project `2026-05may-11mon-fastapi-learning` at `/home/DO_NOT_DELETE_EXTRA/WORK/2026_05May_11Mon_fastapi_learning`
➜  2026_05May_11Mon_fastapi_learning git:(master) ✗ 
```

# update the python version to one which we want

```
uv python install 3.14.5
uv python pin 3.14.5
```

# install venv

```
uv venv
```

# activate venv

```
source .venv/bin/activate
```

# add .gitignore

```
echo "*" > .venv/.gitignore
```


# install fastapi

Use uv add instead, which maintains `pyproject.toml` and `uv.lock` automatically:

```
uv add "fastapi[standard]"
```

the above created `uv.lock` and adds the fastapi to the `pyproject.toml`

# uv run

uv run automatically uses the project's `.venv` python without needing to activate it.

```
uv run which python

uv run python --version
```

# uv run python main.py

```
➜  2026_05May_11Mon_fastapi_learning git:(master) ✗ uv run python main.py
Hello from 2026-05may-11mon-fastapi-learning!
```


# copy minimal fastapi code to main.py

main.py

```
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}
```

# run fastapi

```
➜  2026_05May_11Mon_fastapi_learning git:(master) ✗ uv run fastapi dev

   FastAPI   Starting development server 🚀
 
             Searching for package file structure from directories with __init__.py files
             Importing from /home/DO_NOT_DELETE_EXTRA/WORK/2026_05May_11Mon_fastapi_learning
 
    module   🐍 main.py
 
      code   Importing the FastAPI app object from the module with the following code:
 
             from main import app
 
       app   Using import string: main:app
 
    server   Server started at http://127.0.0.1:8000
    server   Documentation at http://127.0.0.1:8000/docs
 
       tip   Running in development mode, for production use: fastapi run
 
             Logs:
 
      INFO   Will watch for changes in these directories: ['/home/DO_NOT_DELETE_EXTRA/WORK/2026_05May_11Mon_fastapi_learning']
      INFO   Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
      INFO   Started reloader process [15149] using WatchFiles
      INFO   Started server process [15158]
      INFO   Waiting for application startup.
      INFO   Application startup complete.

```

# git related

## push an existing repository from the command line
```
git remote add origin git@github.com:sant527/fastapi_project.git
git branch -M main
git push -u origin main
```

## generate ssh key

```
➜  2026_05May_11Mon_fastapi_learning git:(main) ✗ ssh-keygen 
Generating public/private ed25519 key pair.
Enter file in which to save the key (/home/simha/.ssh/id_ed25519): /home/simha/.ssh/id_github_personal_ed25519
Enter passphrase (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in /home/simha/.ssh/id_github_personal_ed25519
Your public key has been saved in /home/simha/.ssh/id_github_personal_ed25519.pub
The key fingerprint is:
SHA256:ncJhvMYPrWkHqDZ0dOxKvr1T/1yJdHjWd0VQdWTPahI simha@gauranga
The key's randomart image is:
+--[ED25519 256]--+
|              .+O|
|       o       +o|
|      . *   E   +|
|     . B = . ...o|
|    . + S + .oo++|
|   . = o B. .o= +|
|    + o +.o. . ..|
|   . . +..  .. . |
|      . oo   .o  |
+----[SHA256]-----+
➜  2026_05May_11Mon_fastapi_learning git:(main) ✗ cat /home/simha/.ssh/id_github_personal_ed25519.pub 
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINadma5/hCuzTXfzF8vMT/70ZVWR6gxTe6D/+nrVUW7K simha@gauranga
➜  2026_05May_11Mon_fastapi_learning git:(main) ✗ 
```


## how to use different keys for different git repos

# SSH Config for Multiple Keys

## Edit `~/.ssh/config`

```
# GitHub - personal
Host github-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_github_personal_ed25519

# GitHub - work
Host github-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_github_work_ed25519

# GitLab
Host gitlab.com
    HostName gitlab.com
    User git
    IdentityFile ~/.ssh/id_gitlab_ed25519
```

## Set Remote URL Using the Alias

```bash
# Personal repo
git remote set-url origin git@github-personal:sant527/fastapi_project.git

# Work repo
git remote set-url origin git@github-work:myorg/work-project.git
```

## Test Each Connection

```bash
ssh -T git@github-personal
ssh -T git@github-work
```

## Key Idea

The **Host alias** in `~/.ssh/config` replaces `github.com` in the remote URL.
That is how SSH knows which key to use per repo.


## testing

```
➜  2026_05May_11Mon_fastapi_learning git:(main) ✗ ssh -T git@github-personal                                           
Hi sant527! You've successfully authenticated, but GitHub does not provide shell access.
➜  2026_05May_11Mon_fastapi_learning git:(main) ✗ 
```

