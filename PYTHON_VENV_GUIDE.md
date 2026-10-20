# Python virtual environments (PowerShell)

A virtual environment (`.venv`) is a project-local Python setup. It keeps that project's installed packages separate from other projects and from system Python. The `(.venv)` marker in the prompt means an environment is active, but it does not tell you which one; check its path before installing packages.

## One environment per project

This repository has multiple Python projects. Keep a separate environment in each project folder, for example:

- `data-collector\.venv`
- `trend-intelligence\.venv`

Packages installed in one environment are not automatically available in the other. The `.venv` folders are generated locally and should not be committed to Git.

## Set up `data-collector` for the first time

Open PowerShell and run:

```powershell
cd C:\Users\Janith\Desktop\Research-backend\data-collector
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`py -m venv .venv` creates the environment in the current folder. Activate it before installing or running the project's Python tools. `python -m pip` runs pip through the selected Python and avoids depending on a possibly stale `pip.exe` shortcut.

If PowerShell blocks activation with an execution-policy error, you can use the environment's Python directly without activating it:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Alternatively, activation can be enabled for just the current PowerShell window with:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Set up another project

Use that project's own folder and requirements file. For example:

```powershell
cd C:\Users\Janith\Desktop\Research-backend\trend-intelligence
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If it has a `requirements.txt`, install it with `python -m pip install -r requirements.txt` while that environment is active. Do not point one project at another project's `.venv`.

## Start work later

Each new terminal starts without an activated environment. Activate the one belonging to the project you are working in:

```powershell
cd C:\Users\Janith\Desktop\Research-backend\data-collector
.\.venv\Scripts\Activate.ps1
```

Confirm the active Python before installing packages or running commands:

```powershell
python -c "import sys; print(sys.executable)"
```

The path should end in the project's `.venv\Scripts\python.exe`. You can also check:

```powershell
python --version
python -m pip --version
Get-Command python
Get-Command pip
```

Use `python -m pip` for package commands. If `pip --version` reports a path in a different project or a missing Python executable, use `python -m pip` after confirming `sys.executable` points to the intended `.venv`.

## Common package commands

Run these with the intended project environment active:

```powershell
python -m pip install package-name       # install a package
python -m pip install -r requirements.txt # install project dependencies
python -m pip list                        # show installed packages
python -m pip show package-name           # show package details
python -m pip freeze                      # list exact installed versions
python -m pip freeze > requirements.txt   # save installed versions (only when appropriate for the project)
```

Run a script with the environment's Python, for example:

```powershell
python .\yt_collector.py stats
```

## Deactivate

When finished, or before switching projects, run:

```powershell
deactivate
```

This only deactivates the environment in the current terminal. It does not delete the environment or uninstall packages. Activate the other project's `.venv` after changing into its folder.

## Repair or recreate an environment

Virtual environments contain paths to the Python installation and folder that created them. Moving or renaming a project can make their launchers stale. If an environment is broken, recreate it in that project's folder.

First deactivate it if active, then remove only that project's `.venv` folder and create it again:

```powershell
deactivate
Remove-Item -Recurse -Force .\.venv
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run `Remove-Item` only after `cd`-ing to the project whose `.venv` you intend to replace. It deletes that environment and its installed packages; it does not delete your source code. If there is no `requirements.txt`, install the dependencies documented by that project instead.

## Quick checklist

1. `cd` into the project folder.
2. Activate that folder's `.venv`.
3. Check `python -c "import sys; print(sys.executable)"` if unsure.
4. Install packages with `python -m pip ...`.
5. Run the project's commands.
6. Use `deactivate` when done or before switching projects.
