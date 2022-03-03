from event_processors import CommitRange

def test_commit_range__new_branch():
    'These show up as a starting commit of 0000000'
    cr = CommitRange('url', '0000000000000000000000000000000000000000', 'end')
    assert cr.start is None

def test_commit_range__standard():
    cr = CommitRange('url', 'start', 'end')
    assert cr.start == 'start'
