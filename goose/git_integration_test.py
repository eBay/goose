from . import event_processors as ep
from git import Git, Repo
import tempfile
import os
import pytest
import subprocess


@pytest.mark.slow
def test_git():
    with tempfile.TemporaryDirectory() as tmpdir:
        for cmd in [
                'git init',
                'git config user.email "me@example.org"',
                'git config user.name "Me"',
                'echo 1 > first',
                'git add first',
                'git commit -am first',
                'echo 2 > second',
                'git add second',
                'git commit -am second',
                'echo 3 > second',
                'git add second',
                'git commit -am update-second',
                'rm first',
                'git add first',
                'git commit -am remove-first',
        ]:
            subprocess.run(cmd, cwd=tmpdir, shell=True, check=True)


        result = subprocess.run('git log --pretty=%H', shell=True, cwd=tmpdir, capture_output=True, check=True)
        shas = result.stdout.split()

        latestCommit = shas[0].decode('utf-8')
        firstCommit = shas[-1].decode('utf-8')

        # NOTE: The file git repo in the temp directory here gets re-cloned by the underlying code.
        commit_range = ep.CommitRange('file://'+ tmpdir, firstCommit, latestCommit)

        assert commit_range.files_changed() == {'first', 'second'}
        assert commit_range.get_file_contents_at_latest(['second']) == {'second': '3\n'}
