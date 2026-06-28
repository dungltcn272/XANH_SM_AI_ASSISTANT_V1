from __future__ import annotations

import logging


def get_logger(name: str = "xanhsm") -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    return logging.getLogger(name)


logger = get_logger()
