from threading import Thread, current_thread
from Queue import Queue
from random import randint
from time import sleep


def worker(q):
    while True:
        item = q.get()
        t = randint(3, 8)
        print "Thread: {} Value: {} - will sleep for {} seconds".format(current_thread().name, item, t)
        sleep(t)
        q.task_done()


def main(source, num_worker_threads):
    q = Queue()
    for i in range(num_worker_threads):
        t = Thread(target=worker, args=(q, ))
        t.daemon = True
        t.start()

    print "putting things into the queue..."
    for item in source:
        q.put(item)

    print "waiting for all items to be processed..."
    q.join()
    print "done !!!"


if __name__ == '__main__':
    src = range(20)
    wrkr_threads = 8
    main(src, wrkr_threads)
