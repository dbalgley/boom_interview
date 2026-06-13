"""Logging configuration for command-line execution."""

import logging


def configure_logging() -> None:
    """Configure default CLI logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
