import logging

def logging_conf():
    logger = logging.getLogger()
    logger.handlers.clear()

    handler = logging.FileHandler("/medicalplaza/logging.log", mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s : %(levelname)s : %(message)s"))

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)