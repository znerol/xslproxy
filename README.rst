XSL Proxy
=========

.. image:: https://travis-ci.com/znerol/xslproxy.svg?branch=master
    :target: https://travis-ci.com/znerol/xslproxy


Xsl transforming reverse proxy based on twisted_ and lxml_

.. _twisted: https://twistedmatrix.com/
.. _lxml: https://lxml.de/


Installation
------------

::

   python3 -m pip install xslproxy


Usage
-----

::

   Usage: twist [options] plugin [plugin_options] xslproxy [options]
   Options:
         --backend=  Url to backend, no trailing slash [default: http://localhost]
         --help      Display this help and exit.
         --listen=   Listen port (strports syntax) [default: tcp:8080]
         --path=      [default: A directory with xsl files]
         --version   Display Twisted version and exit.


Requests to one of the proxy endpoints will be forwarded to the backend. When a
successful result is returned from the backend, content is transformed using
the specified XSL stylesheets and sent to the client. The following proxy
endpoints are available:

/transform/{XSLPARAMS}
  All stylesheets and parameters specified in XSLPARAMS are applied and to the
  backend response and the result is returned to the client with
  ``Content-Type`` header set to ``application/xml``, ``text/html`` or
  ``text/plain`` according to the ``method`` specified in the ``<xsl:output>``
  element of the last stylesheet in the chain.

The ``XSLPARAMS`` path segement takes the following ``key=value`` pairs. Each
pair separated by the ampersand (``&``) character:

xsl[]
  Relative path to a stylesheet on the server (without ``.xsl`` or ``.xslt``
  extension). This parameter can be specified multiple times.
xp[stylesheet-key][param-key]
  XPath parameter with the name ``param-key`` for the stylesheet specified in
  ``stylesheet-key``. The latter need to match one of the values specified via
  ``xsl[]`` parameter.
xs[stylesheet-key][param-key]
  String parameter with the name ``param-key`` for the stylesheet specified in
  ``stylesheet-key``. The latter need to match one of the values specified via
  ``xsl[]`` parameter.


License
-------

The software is subject to the AGPLv3_ or later license.

.. _AGPLv3: https://www.gnu.org/licenses/agpl-3.0.en.html
