import logging
import sys

class logger2(logging.getLoggerClass()):
    def __init__(self, arg):
        super(logger2, self).__init__(arg)

    def trace(self, message):
        self.log(5, message)

logging.addLevelName(5, 'TRACE')
default_log_level = 'INFO'

def getLogger(log_level, log_config):
    global logging
    log_level = log_level if log_level else default_log_level
    if log_config:
        import logging.config
        try:
            logging.config.fileConfig(log_config)
        except Exception as e:
            sys.stderr.write('Problem with log config file: ' + e.message)

    log = logger2('s3-index-gen')
    try:
        log.setLevel(log_level)
    except Exception as err:
        sys.stdout.write('Error with log level: "%s"' % err.message)
        exit(1)
    if not log_config:
        log.addHandler(logging.StreamHandler(sys.stdout))
    return log

def getLoggingLevels():
    levels_numbers = []
    for lvl in logging._levelNames.keys():
        if type(lvl) == int:
            if not lvl: continue # Pass by NOTSET
            levels_numbers.append(lvl)
    levels_numbers = sorted(levels_numbers, reverse=True)
    return [logging._levelNames[lvl] for lvl in levels_numbers]