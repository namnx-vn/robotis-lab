# One-time import of the existing RL-H25 v0.2.1 local source

The GitHub repository was created after the local Webots project. At the time this document was written, `master` contains only the initial README. **Do not treat this documentation-only PR as a source import.**

## Operator's existing folder
The most recent ChatGPT-provided artifact is `robotis-lab-v021-controlled-disturbance.zip`, with a `robotis-lab-v021/` root folder. Work on a *copy* of the extracted local source, and compare it to any custom edits you have made on the Mac. Do not overwrite unsaved Webots or controller work.

## Import without nesting the project directory
```bash
cd ~/my_learning/robotis-lab
git clone https://github.com/namnx-vn/robotis-lab.git robotis-lab-repo
cd robotis-lab-repo
git checkout -b feat/import-rlh25-v021
# Replace path with the actual extracted v0.2.1 source directory:
rsync -av --exclude='.git' --exclude='__pycache__' \
  --exclude='.env' --exclude='logs/' \
  ../robotis-lab-v021/ ./
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
git status --short
git add README.md AGENTS.md configs docs simulation tools tests tasks experiments .gitignore .env.example
git commit -m "Import RL-H25 v0.2.1 Webots simulation and disturbance tests"
git push -u origin feat/import-rlh25-v021
```

Open a pull request targeting `master`. Inspect the diff for accidental logs/credentials before approval. Once merged, future changes can be committed to feature branches by the connected AI GitHub capability without requiring ZIP uploads.

### Native Mac smoke experiment
```bash
python3 tools/run_disturbance_trials.py \
 --webots /Applications/Webots.app/Contents/MacOS/webots \
 --pairs 1 --axis pitch --force 0.10 --pulse 0.112 --duration 14
```
A one-pair comparison may intentionally say `INCONCLUSIVE` (insufficient paired trials), even though files are written. Five or more pairs and observed perturbation are required before evaluating PID effectiveness.

## Current limitations
- Historical native Webots baseline 5/5 exists only as owner-shared terminal output in the conversation, **not as versioned CSV evidence**.
- A previous manual disturbance entered `FAULT excessive_tilt`. Do not silently raise safety cutoffs or claim PID success.
- P3 gait remains blocked until actual standardized force-response experiments, plus visual contact checks.
