from tempfile import NamedTemporaryFile
from twisted.internet import defer, protocol, threads
from twisted.logger import Logger
from twisted.python.compat import urlquote
from twisted.web import http, resource, server
from urllib.parse import urlsplit
import os
import shutil


class ExtractionProxyClient(http.HTTPClient):
    log = Logger()

    extraction = None
    hostport = ""
    path = ""
    downstream = None

    def connectionMade(self):
        self._response_finished = False
        self._response_capture = False
        self._response_file = None
        self._response_headers = []
        self._response_processing = False

        # Proxy downstream request to downstream.
        path = self.path
        query = urlsplit(self.downstream.uri).query
        if query:
            path += b"?" + query
        self.sendCommand(self.downstream.method, path)

        # Headers
        self.sendHeader(b"host", self.hostport)
        self.sendHeader(b"connection", b"close")

        strip_headers = [
            b"host", b"connection", b"proxy-connection", b"keep-alive"]
        request_headers = self.downstream.requestHeaders.getAllRawHeaders()
        for header, values in request_headers:
            if header.lower() not in strip_headers:
                for value in values:
                    self.sendHeader(header, value)
        self.endHeaders()

        # Body
        self.downstream.content.seek(0, 0)
        self.log.debug("start sending request body")
        threads.deferToThread(
            shutil.copyfileobj, self.downstream.content, self.transport
        ).addCallback(lambda _: self.log.debug(
            "request body sent")
        ).addErrback(lambda error: self.log.failure(
            "request body failed to send", failure=error)
        )

    def handleStatus(self, version, code, message):
        self._response_capture = (int(code) == 200)
        self.log.info(f"response capture: {self._response_capture}")

        if self._response_capture:
            self._response_file = NamedTemporaryFile(delete=False)

        self.downstream.setResponseCode(int(code), message)

    def handleHeader(self, key, value):
        # t.web.server.Request sets default values for these headers in its
        # "process" method. When these headers are received from the remote
        # server, they ought to override the defaults, rather than append to
        # them.
        if key.lower() in [b"server", b"date", b"content-type"]:
            self.downstream.responseHeaders.setRawHeaders(key, [value])
        else:
            self.downstream.responseHeaders.addRawHeader(key, value)

    def handleResponsePart(self, buf):
        if self._response_capture:
            self._response_file.write(buf)
        else:
            self.downstream.write(buf)

    def handleResponseEnd(self):
        if self._response_capture:
            # This method potentially is called multiple times. Thus it is
            # necessary to guard against that.
            if not self._response_processing:
                self._response_processing = True
                self._processResponse()
        else:
            self._endResponse()

    @defer.inlineCallbacks
    def _processResponse(self):
        self.log.info("response process start")
        self._response_file.close()

        response_headers = self.downstream.responseHeaders
        response_headers.removeHeader(b"Content-Type")
        response_headers.removeHeader(b"Content-Length")

        try:
            content, contentType = yield self.extraction.extract(
                self._response_file.name)

            response_headers.setRawHeaders(
                b"Content-Type", [contentType])
            response_headers.setRawHeaders(
                b"Content-Length", [str(len(content)).encode()])

            self.downstream.write(content)

        except FileNotFoundError:
            self.downstream.setResponseCode(404, b"Not found")
            self.downstream.responseHeaders.addRawHeader(
                b"Content-Type", b"text/html")
            self.downstream.write(b"<H1>Not found</H1>")
            self.downstream.finish()
            self.log.error("response process no data was extracted")

        except Exception:
            self.downstream.setResponseCode(501, b"Gateway error")
            self.downstream.responseHeaders.addRawHeader(
                b"Content-Type", b"text/html")
            self.downstream.write(b"<H1>Could process response</H1>")
            self.downstream.finish()
            self.log.failure("response process failure")

        finally:
            os.remove(self._response_file.name)
            self._endResponse()
            self.log.info("response process end")

    def _endResponse(self):
        """
        Finish the original request, indicating that the response has been
        completely written to it, and disconnect the outgoing transport.
        """
        if not self._response_finished:
            self._response_finished = True
            self.downstream.finish()
            self.transport.loseConnection()


class ExtractionProxyClientFactory(protocol.ClientFactory):

    def __init__(self, extraction, hostport, path, downstream):
        self._extraction = extraction
        self._hostport = hostport
        self._path = path
        self._downstream = downstream

    def buildProtocol(self, addr):
        proto = protocol.ClientFactory.buildProtocol(self, addr)
        proto.extraction = self._extraction
        proto.hostport = self._hostport
        proto.path = self._path
        proto.downstream = self._downstream
        return proto

    def clientConnectionFailed(self, connector, reason):
        """
        Report a connection failure in a response to the incoming request as
        an error.
        """
        self._downstream.setResponseCode(501, b"Gateway error")
        self._downstream.responseHeaders.addRawHeader(
            "Content-Type", b"text/html")
        self._downstream.write(b"<H1>Could not connect</H1>")
        self._downstream.finish()


class ExtractionReverseProxyResource(resource.Resource):
    """
    see twisted.web.proxy.ReverseProxyResource
    """

    def __init__(self, extraction, backend, hostport, path):
        """
        see ReverseProxyResource.__init__()
        """
        super().__init__()
        self._extraction = extraction
        self._backend = backend
        self._hostport = hostport
        self._path = path

    def getChild(self, path, request):
        """
        see ReverseProxyResource.getChild()
        """
        return ExtractionReverseProxyResource(
            self._extraction, self._backend, self._hostport,
            self._path + b"/" + urlquote(path, safe=b"").encode("utf-8"))

    def render(self, request):
        """
        see ReverseProxyResource.render()
        """
        clientFactory = ExtractionProxyClientFactory.forProtocol(
            ExtractionProxyClient, self._extraction, self._hostport,
            self._path, request)
        self._backend.connect(clientFactory)
        return server.NOT_DONE_YET
