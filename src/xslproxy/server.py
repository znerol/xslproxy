from twisted.web import http, server


class HTTPChannel(http.HTTPChannel):
    """
    A twisted L{http.HTTPChannel} with support for huge urls (up to 64k).
    """
    totalHeadersSize = 0xFFFF
    MAX_LENGTH = 0xFFFF


class Site(server.Site):
    """
    A twisted L{server.Site} with support for huge urls (up to 64k).
    """
    protocol = HTTPChannel
