from twisted.internet import defer, threads
from twisted.web import resource
from xslproxy.web import ExtractionReverseProxyResource

# Use parser from defusedxml.
from defusedxml.lxml import parse as defusedxml_parse

# XSLT is not present in defusedxml, explicitely get the one from lxml.
from lxml import etree

import glob
import os
import urllib.parse


class XslTransformationExtraction:

    def __init__(self, transformations, params, content_type):
        self._transformations = transformations
        self._params = params
        self._content_type = content_type

    @defer.inlineCallbacks
    def extract(self, filename):
        doc = yield threads.deferToThread(defusedxml_parse, filename)

        for key, transformation in self._transformations:
            doc = transformation(doc, **self._params.get(key, {}))

        return bytes(doc), self._content_type


class NoStylesheetsResource(resource.ErrorPage):

    def __init__(self):
        super().__init__(
            400,
            "Bad Request",
            "No stylesheets defined, please provide at least one xsl[] param",
        )


class XslTransformationReverseProxyResource(resource.Resource):

    def __init__(self, repository, backend, hostport, path):
        super().__init__()
        self._repository = repository
        self._backend = backend
        self._hostport = hostport
        self._path = path
        self._parser = XslQueryStringParser()
        self._output_method = XslOutputMethodDetection()
        self._content_type_map = {
            "html": b"text/html",
            "text": b"text/plain",
            "xml": b"application/xml",
        }

    def getChild(self, paramspec, request):
        xsls, params = self._parser.parse(paramspec)

        # Load stylesheets
        try:
            stylesheets = [(key, self._repository.load(key)) for key in xsls]
        except XslRepositoryNoCandidateError:
            return resource.NoResource(
                "One of the specified stylesheets was not found on the server"
            )

        if len(stylesheets) == 0:
            return NoStylesheetsResource()

        # Detect the output method of the last stylesheet and map it to
        # content-type.
        method = self._output_method.detect(stylesheets[-1][1])
        content_type = self._content_type_map[method]

        # Tranformations
        transformations = [(key, etree.XSLT(doc)) for key, doc in stylesheets]

        extraction = XslTransformationExtraction(
            transformations, params, content_type)
        return ExtractionReverseProxyResource(
            extraction, self._backend, self._hostport, self._path)


class XslOutputMethodDetection:
    """
    Determines whether a given stylesheet produces text, html or xml by looking
    at the method attribute of the <xsl:output/> element.
    """

    default_method = "xml"

    def detect(self, doc):
        result = self.default_method

        output = doc.xpath(
            "/xsl:stylesheet/xsl:output",
            namespaces={
                "xsl": "http://www.w3.org/1999/XSL/Transform"
            }
        )

        if (len(output) > 0):
            result = output[0].attrib.get("method", self.default_method)

        return result


class XslQueryStringParser:
    """
    Parses a query string into a list of xsl stylesheet keys and a  dictionary
    of xslt parameters.
    """

    def parse(self, qs):
        qsl = urllib.parse.parse_qsl(qs.decode(), strict_parsing=True)

        xsls = [value for name, value in qsl if name == "xsl[]"]

        params = {}

        # Parse xpath params
        # e.g., xp[my-stylesheet][position]=4
        for key in xsls:
            namepfx = f"xp[{key}]"
            pfxlen = len(namepfx)
            params.setdefault(key, {}).update([
                (name[pfxlen+1:-1], etree.XPath(value))
                for name, value in qsl
                if name.startswith(namepfx)
            ])

        # Parse string params,
        # e.g., sp[my-stylesheet][param-name]=hello world!
        for key in xsls:
            namepfx = f"sp[{key}]"
            pfxlen = len(namepfx)
            params.setdefault(key, {}).update([
                (name[pfxlen+1:-1], etree.XSLT.strparam(value))
                for name, value in qsl
                if name.startswith(namepfx)
            ])

        return xsls, params


class XslRepositoryError(Exception):
    pass


class XslRepositoryNoCandidateError(XslRepositoryError):
    pass


class XslRepositoryTooManyCandidatesError(XslRepositoryError):
    pass


class XslRepository:

    def __init__(self, path):
        self._path = os.path.realpath(path)

    def load(self, key):
        candidates = [
            c for c in glob.glob(os.path.join(self._path, f"{key}.*"))
            if os.path.splitext(c)[1].lower() in [".xsl", ".xslt"]
            and os.path.commonprefix((c, self._path)) == self._path
        ]

        if len(candidates) == 0:
            raise XslRepositoryNoCandidateError
        elif len(candidates) > 1:
            raise XslRepositoryTooManyCandidatesError

        return etree.parse(candidates[0])
