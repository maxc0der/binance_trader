import logging

logFormatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)s][%(funcName)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)
fileHandler = logging.FileHandler("{0}.log".format('log'))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)