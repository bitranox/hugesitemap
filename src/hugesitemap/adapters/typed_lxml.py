# pyright: reportMissingTypeStubs=false, reportAttributeAccessIssue=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
"""Typed facade over the untyped ``lxml.etree`` surface used by the writer.

``lxml`` ships no type stubs, so under pyright ``strict`` every ``etree.X`` call
is reported as unknown. Rather than disable those rules project-wide (which would
blind the checker to real ``Unknown`` regressions in our own code), this module
is the single, narrowly-scoped boundary where the lxml-related rules are turned
off via the file-level pragma above. Every other module imports these fully
typed wrappers and stays strict-clean.

Contents:
    * :data:`XmlElement` - opaque element alias.
    * :data:`XmlSyntaxError` - the lxml parse-error exception type.
    * :func:`new_element`, :func:`child`, :func:`set_attribute`, :func:`set_text`.
    * :func:`serialize`, :func:`parse` - serialize and re-parse documents.
"""

from __future__ import annotations

from typing import Any

from lxml import etree as _etree

XmlElement = Any
"""Opaque alias for an lxml element (its concrete type is unknown to pyright)."""

XmlSyntaxError: type[Exception] = _etree.XMLSyntaxError
"""The exception lxml raises on malformed XML during re-parse validation."""


def new_element(qname: str, nsmap: dict[str | None, str]) -> XmlElement:
    """Create a root element with the given qualified name and namespace map."""
    return _etree.Element(qname, nsmap=nsmap)


def child(parent: XmlElement, qname: str) -> XmlElement:
    """Create and append a child element under ``parent``."""
    return _etree.SubElement(parent, qname)


def set_attribute(element: XmlElement, qname: str, value: str) -> None:
    """Set an attribute on ``element``."""
    element.set(qname, value)


def set_text(element: XmlElement, text: str) -> None:
    """Set the text content of ``element``."""
    element.text = text


def serialize(root: XmlElement) -> bytes:
    """Serialize ``root`` to a pretty-printed UTF-8 XML document with a declaration."""
    result: bytes = _etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)
    return result


def parse(data: bytes) -> None:
    """Parse ``data`` to verify well-formedness, raising :data:`XmlSyntaxError` on failure."""
    _etree.fromstring(data)


__all__ = [
    "XmlElement",
    "XmlSyntaxError",
    "child",
    "new_element",
    "parse",
    "serialize",
    "set_attribute",
    "set_text",
]
