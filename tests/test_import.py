def test_import_pyabundance():
    import pyabundance
    from pyabundance import pcount

    assert pyabundance.__version__ == "1.0.0rc1"
    assert callable(pcount)
