import event_processors as ep
from git import Git, Repo
import tempfile
import os
import pytest

@pytest.mark.slow
def test_git_file_contents():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Repo.init(tmpdir)
        new_file = os.path.join(tmpdir, 'myfile')
        with open(new_file, 'w') as f:
            f.write("WORKS")
        repo.index.add([new_file])
        commit = repo.index.commit("Added new file")
        commit_info = ep.CommitInfo('file://'+ tmpdir, commit.hexsha)


        output = ep.get_file_contents_at_sha(['myfile'], commit_info)
        assert output['myfile'] == 'WORKS'
