import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import start_tool

def test_parse_arguments_no_args():
    args = start_tool.parse_arguments([])
    assert not args.repair


def test_parse_arguments_repair():
    args = start_tool.parse_arguments(["--repair"])
    assert args.repair
