from blacksmith.service._sync.client import SyncClientFactory
from pyramid.interfaces import IRequestExtensions


def test_includeme(config):
    ext = config.registry.queryUtility(IRequestExtensions)
    assert "blacksmith" in ext.descriptors


def test_req_attr(dummy_request):
    assert isinstance(dummy_request.blacksmith, SyncClientFactory)
