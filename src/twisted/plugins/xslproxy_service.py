from twisted.application.service import ServiceMaker

XslProxyService = ServiceMaker(
    "Xsl Proxy Service",
    "xslproxy.service",
    "XSL transforming reverse proxy",
    "xslproxy")
