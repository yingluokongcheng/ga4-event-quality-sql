"""One-time setup; downloading/installing needs internet, dashboard use does not."""
from pathlib import Path
import subprocess,sys,os,venv
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
if sys.version_info<(3,10):raise SystemExit('Python 3.10+ required; Python 3.12 is tested.')
env=ROOT/'.venv'
py=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
if not py.exists():venv.EnvBuilder(with_pip=True).create(env)
def run(*args):subprocess.run([str(py),*args],check=True)
run('-m','pip','install','-r',str(ROOT/'requirements-lock.txt'))
run('scripts/download.py')
run('scripts/audit.py')
run('scripts/build_analysis.py')
run('scripts/report_analysis.py')
print('READY. Windows: double-click Start_dashboard.cmd. Other platforms: .venv/bin/python -m streamlit run app.py')
