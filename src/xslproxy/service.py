from twisted.application import strports
from twisted.internet import endpoints, reactor
from twisted.python import usage
from twisted.web import resource, server
from xslproxy.xsl import XslRepository, XslTransformationReverseProxyResource
from urllib.parse import urlsplit


class Options(usage.Options):
    optParameters = [
        ["backend", "-b", "http://localhost",
            "Url to backend, no trailing slash"],
        ["listen", "-l", "tcp:8080",
            "Listen port (strports syntax)"],
        ["path", "-p",
            "A directory with xsl files"],
    ]


def makeService(options):
    parts = urlsplit(options["backend"])
    host = parts.hostname
    path = parts.path.encode("utf-8")

    if parts.scheme == "http":
        port = int(parts.port) if parts.port is not None else 80
        backend_strports = f"tcp:{host}:{port}"
    else:
        port = int(parts.port) if parts.port is not None else 443
        backend_strports = f"ssl:{host}:{port}"

    hostport = (f"{host}:{port}" if parts.port else f"{host}").encode("ascii")

    backend = endpoints.clientFromString(reactor, backend_strports)

    repository = XslRepository(options["path"])
    root = resource.Resource()
    root.putChild(b"transform", XslTransformationReverseProxyResource(
        repository, backend, hostport, path))
    return strports.service(options["listen"], server.Site(root))
