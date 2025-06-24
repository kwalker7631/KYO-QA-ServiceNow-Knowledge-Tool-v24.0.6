import shutil

import file_utils


def test_copy_file_safely_retries(tmp_path, mocker):
    src = tmp_path / "src.txt"
    src.write_text("data")
    dest = tmp_path / "dest.txt"

    call_count = {"n": 0}
    real_copy = shutil.copy2

    def fake_copy(s, d, *, follow_symlinks=True):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise IOError("fail")
        return real_copy(s, d, follow_symlinks=follow_symlinks)

    mocker.patch("file_utils.shutil.copy2", side_effect=fake_copy)

    assert file_utils.copy_file_safely(src, dest, retries=2, wait_time=0)
    assert call_count["n"] == 2
    assert dest.read_text() == "data"

