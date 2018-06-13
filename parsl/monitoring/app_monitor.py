import time
from multiprocessing import Process
import psutil
import os
from parsl.db_logger import get_db_logger

simple = ["cpu_num", 'cpu_percent', 'create_time', 'cwd', 'exe', 'memory_percent', 'nice', 'name', 'num_threads', 'pid', 'ppid', 'status', 'username']


def monitor(pid, task_id, db_logger_config, run_id):
    logger = get_db_logger(enable_es_logging=False) if db_logger_config is None else get_db_logger(**db_logger_config)

    logger.info("starting monitoring for {} on {}".format(pid, os.getpid()))
    pm = psutil.Process(pid)
    pm.cpu_percent()
    while True:
        children = pm.children(recursive=True)
        d = {"psutil_process_" + str(k): v for k, v in pm.as_dict().items() if k in simple}
        d["psutil_cpu"] = psutil.cpu_count()
        d["task_run_id"] = run_id
        d["task_id"] = task_id
        for n in ["user", "system", "children_user", "children_system"]:
            d["psutil_process_" + n] = getattr(pm.cpu_times(), n)
        for child in children:
            try:
                c = {"psutil_process_child_" + str(k): v for k, v in child.as_dict().items() if (k in simple and v > d.get("psutil_process_child_" + str(k), 0))}
            except TypeError:
            # ignore an error that occurs if compare the comparison is comparing against a bad or non existant value by simply replacing it with the newer child's info
                c = {"psutil_process_child_" + str(k): v for k, v in child.as_dict().items() if k in simple}
            d.update(c)
        logger.info("test", extra=d)
        time.sleep(4)


def monitor_wrapper(f, task_id, db_logger_config, run_id):
    def wrapped(*args, **kwargs):
        p = Process(target=monitor, args=(os.getpid(), task_id, db_logger_config, run_id))
        p.start()
        result = f(*args, **kwargs)
        p.terminate()
        return result
    return wrapped


def log_task_info(task_id, task):
    host = 'search-parsl-logging-test-2yjkk2wuoxukk2wdpiicl7mcrm.us-east-1.es.amazonaws.com'
    port = 443
    handler = CMRESHandler(hosts=[{'host': host,
                                   'port': port}],
                           use_ssl=True,
                           auth_type=CMRESHandler.AuthType.NO_AUTH,
                           es_index_name="my_python_index",
                           es_additional_fields={'Campaign': "test", 'Username': "yadu"})

    logger = logging.getLogger("ParslElasticsearch")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    d = {"task_" + str(k): v for k, v in task.items()}
    d["run_id"] = run_name
    logger.info("Tast info for task {}".format(task_id), extra=d)


if __name__ == "__main__":
    def f(x):
        for i in range(10**x):
            continue

    wrapped_f = monitor_wrapper(f, 0)
    wrapped_f(9)
