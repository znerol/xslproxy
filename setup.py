from setuptools import setup

setup(
    name="xslproxy",
    version="1.0.1",
    description="Xsl transforming reverse proxy based on twisted",
    long_description=open('README.rst').read(),
    author="Lorenz Schori",
    author_email="lo@znerol.ch",
    url="https://github.com/znerol/xslproxy",
    package_dir={"": "src"},
    packages=[
        "xslproxy",
        "twisted.plugins"
    ],
    package_data={
        "twisted.plugins": [
            "twisted/plugins/xslproxy_service.py",
        ]
    },
    python_requires=">=3.5",
    install_requires=[
        "Twisted[tls]",
        "defusedxml",
        "zope.interface",
        'lxml'
    ],
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Plugins",
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: Proxy Servers",
    ],
)
