"""Use the operating system certificate store for outbound HTTPS."""

import truststore


def use_system_certificates() -> None:
    """Trust OS roots, including a local proxy CA that certifi does not ship."""
    truststore.inject_into_ssl()
