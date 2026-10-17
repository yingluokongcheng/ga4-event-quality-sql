"""Download a pinned, third-party GA4 event extract; no Google Cloud account."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPO = 'DavidKingGH/dbt_portfolio_project_1'
COMMIT = '41c4ee829b7c18cdb52810686768edfa035a42e0'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify-only', action='store_true')
    args = ap.parse_args()
    manifest_path = ROOT / 'provenance/source_manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    else:
        if args.verify_only:
            raise SystemExit('No manifest. Run download.py first.')
        tree = json.load(urllib.request.urlopen(f'https://api.github.com/repos/{REPO}/git/trees/{COMMIT}?recursive=1', timeout=60))
        assert not tree.get('truncated')
        files = [x for x in tree['tree'] if x['path'].startswith('ga4_data/fct/fact_events/') and x['path'].endswith('.parquet')]
        manifest = {'repository': REPO, 'commit': COMMIT, 'scope': 'third-party flattened event extract, not verified against Google original', 'files': files}
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    def get(entry):
        dest = raw / Path(entry['path']).name
        if not dest.exists():
            if args.verify_only:
                raise RuntimeError(f'Missing {dest}')
            req = f'https://raw.githubusercontent.com/{REPO}/{COMMIT}/{entry["path"]}'
            with urllib.request.urlopen(req, timeout=90) as response:
                content = response.read()
            dest.write_bytes(content)
        content = dest.read_bytes()
        assert len(content) == entry['size'], dest
        assert hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest() == entry['sha'], dest
        digest = hashlib.sha256(content).hexdigest()
        if entry.get('sha256'):
            assert entry['sha256'] == digest, dest
        return {**entry, 'sha256': digest}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        manifest['files'] = list(pool.map(get, manifest['files']))
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(f'Verified {len(manifest["files"])} files; {sum(x["size"] for x in manifest["files"]):,} bytes')

if __name__ == '__main__':
    main()
