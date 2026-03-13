from concurrent.futures import ThreadPoolExecutor


executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="bg-task")


def enqueue(task, *args, **kwargs):
    return executor.submit(task, *args, **kwargs)
