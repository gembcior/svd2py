from pathlib import Path
import pytest


@pytest.fixture
def rootdir():
    path = Path(__file__)
    return path.parent

@pytest.fixture
def datadir(rootdir):
    return rootdir.joinpath("data")


@pytest.fixture
def svddir(datadir):
    return datadir.joinpath("svd")


@pytest.fixture
def yamldir(datadir):
    return datadir.joinpath("yaml")
