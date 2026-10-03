from arcbench.gitinfo import git_info


def test_outside_git_repo_is_unknown_and_dirty(tmp_path):
    info = git_info(tmp_path)
    assert info["sha"] == "unknown"
    assert info["dirty"] is True
