"""Skip automatic publication only for the reviewed licensing snapshot.

The exemption matches only this snapshot directly above BASE; normal runtime
changes and explicit workflow_dispatch retain their publication behavior.
shortcut: this exemption is snapshot-bound; refresh BASE/hashes if rebased.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import sys

BASE = 'a7d47f9a74a04a4f06874e4f16f548449567e178'
EXPECTED = {
    ".github/workflows/main.yml": "dd7beecea438415f162f60362598e5f77e0f661f639639faa28151c6d3fc19ed",
    "LICENSE": "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986",
    "README.md": "c3b331831032ab30be57129aa49dea0f9eea6ff190c9b5beb7b522dd203f8f71",
    "THIRD_PARTY_NOTICES.md": "3d2a63dcb3a95a305cb69953c0d870254cf75f67a194c6373d9695254dafa1f4"
}
SCRIPT = '.github/scripts/licensing-deployment-guard.py'


def licensing_only(parent, files):
    return parent == BASE and files == EXPECTED


def self_test():
    assert licensing_only(BASE, dict(EXPECTED))
    assert not licensing_only('another-parent', dict(EXPECTED))
    assert not licensing_only(BASE, {**EXPECTED, 'runtime.py': 'changed'})
    assert not licensing_only(BASE, {**EXPECTED, 'package.json': 'changed'})
    assert not licensing_only(BASE, {})
    print('licensing deployment guard: 5 checks passed')


def should_deploy():
    event = os.environ.get('GITHUB_EVENT_NAME')
    if event not in ('push', 'workflow_run', 'pull_request') or os.environ.get('GITHUB_REF_TYPE') == 'tag':
        return True
    parent = subprocess.check_output(['git', 'rev-parse', 'HEAD^'], text=True).strip()
    if parent != BASE:
        return True
    paths = subprocess.check_output(
        ['git', 'diff', '--name-only', '-z', BASE, 'HEAD']
    ).decode().split('\0')[:-1]
    if SCRIPT not in paths:
        return True
    files = {
        path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        for path in paths if path != SCRIPT
    }
    return not licensing_only(parent, files)


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        self_test()
    else:
        deploy = should_deploy()
        print('deploy=' + str(deploy).lower())
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write('deploy=' + str(deploy).lower() + '\n')
