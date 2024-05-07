from importlib import metadata

import lektor_imgutils


def test_installed_version_should_match_tested_version():
    assert metadata.version("lektor_imgutils") == lektor_imgutils.__version__
