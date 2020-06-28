from queue import Queue
from threading import Thread, Lock
from tonlib_api import tonlib_api
import time


class TonWorker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks, worker, worker_args):
        Thread.__init__(self)
        self.tasks = tasks
        self.worker = worker
        self.worker_args = worker_args
        self.start()

    def run(self):
        w = self.worker(*self.worker_args)
        print('Worker ready', flush=True)

        while True:
            res, func, arg, timeout = self.tasks.get()
            if func == 'quit':
                self.tasks.task_done()
                print('Worker done', flush=True)
                return
            try:
                #result = getattr(w, func)(arg)
                result = w.run_method(func, arg, timeout=timeout)
            except Exception as e:
                print(e, flush=True)
                result = {'@type': 'error', 'code': 500, 'message': 'Internal error (43)'}
            finally:
                try:
                    res.put_nowait(result)
                except:
                    pass
                self.tasks.task_done()


class TonThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, worker, min_threads=10, max_threads=1000):
        print('Running thread pool', flush=True)
        self.lock = Lock()
        self.worker = worker
        self.min_threads = min_threads
        self.max_threads = max_threads
        self.current_threads = min_threads
        self.load = []

        self.tasks = Queue(max_threads)

        for _ in range(min_threads):
            worker(self.tasks)


    def add_task(self, func, arg, timeout=60):
        """Add a task to the queue"""
        t_start = time.time()

        size = self.tasks.qsize()

        with self.lock:
            if len(self.load) >= self.max_threads:
                self.load = self.load[1:]
            self.load.append(size)

            m = max(self.load)
            k = sum(self.load) / len(self.load)

            if (k > 0.5*self.current_threads or m > 0.9*self.current_threads) and \
                    self.current_threads < self.max_threads:
                self.worker(self.tasks)
                self.current_threads += 1
                print('Need new task. k=%.2f m=%d. Total %d' % (k, m, self.current_threads), flush=True)
            elif k < 0.2*self.current_threads and self.current_threads > self.min_threads:
                try:
                    self.tasks.put((None, 'quit', None, None), block=False)
                    self.current_threads -= 1
                    print('Remove task. Total k=%.2f m=%d. %d' % (k, m, self.current_threads), flush=True)
                except Queue.Full as e:
                    pass

        res = Queue(1)

        try:
            self.tasks.put((res, func, arg, timeout), block=True, timeout=timeout)
        except Queue.Full as e:
            print('Aborted (put) within %f seconds' % (time.time() - t_start), flush=True)
            return {'@type': 'error', 'code': 500, 'message': 'Timeout (Queue full)'}

        try:
            result = res.get(block=True, timeout=timeout)
        except Queue.Empty as e:
            print('Aborted (get) within %f seconds' % (time.time() - t_start), flush=True)
            return {'@type': 'error', 'code': 500, 'message': 'Timeout (Queue wait)'}

        print('Done within %.6f seconds' % (time.time() - t_start), flush=True)
        return result


    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()



if __name__ == '__main__':
    from random import randrange
    from time import sleep

    def ton_worker(tasks):
        return TonWorker(tasks, tonlib_api, ('/home/user/gram/gram-ton/build/tonlib/', global_config))

    with open('test.rocks.config.json', 'r') as f:
        global_config = f.read()

    delays = [randrange(1, 10) for i in range(100)]

    pool = TonThreadPool(ton_worker, 2, 10)


    def run_in_thread(pool):
        result = pool.add_task('raw_getAccountState', '-1:0000000000000000000000000000000000000000000000000000000000000000')
        print(result, flush=True)

    for i, d in enumerate(delays):
        thread = Thread(target = run_in_thread, args = (pool, ))
        thread.start()
        #sleep(d/20.0)
        sleep(0.4)

    pool.wait_completion()
