"""Logging configuration for command-line execution."""

import logging
import sys

from tqdm import tqdm


class TqdmLoggingHandler(logging.StreamHandler):  # type: ignore
    """Logging handler that writes cleanly above an active tqdm progress bar."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record, writing above the tqdm progress bar if active."""
        try:
            message = self.format(record)
            tqdm.write(message)
            self.flush()
        except (OSError, RuntimeError):
            self.handleError(record)


def configure_logging(*, use_tqdm: bool = False) -> None:
    """Configure application logging."""
    handler: logging.Handler

    if use_tqdm:
        handler = TqdmLoggingHandler()
    else:
        handler = logging.StreamHandler(sys.stderr)

    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
