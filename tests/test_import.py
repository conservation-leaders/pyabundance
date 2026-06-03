def test_import_pyabundance():
    import pyabundance
    from pyabundance import pcount

    assert pyabundance.__version__ == "0.1.1"
    assert callable(pcount)
