import os
from threading import Thread
from Queue import Queue


class DirItm:
    def __init__(self, scan_index, thrd_nbr, di_typ, path):
        self.scan_index = scan_index
        self.thrd_nbr = thrd_nbr
        self.di_typ = di_typ
        self.path = path


def dir_worker(thrd_nbr, dq, pq):
    while True:
        dir_item = dq.get()

        pq.put(dir_item)

        list_dir = os.listdir(dir_item.path)
        for item in list_dir:
            path = os.path.join(dir_item.path, item)
            if os.path.isfile(path):
                pq.put(DirItm(dir_item.scan_index, thrd_nbr, 'F', path))
            else:
                dq.put(DirItm(dir_item.scan_index, thrd_nbr, 'D', path))

        dq.task_done()


def path_worker(pq):
    while True:
        item = pq.get()
        print '{}\t{}\t{}\t{}'.format(item.scan_index, item.thrd_nbr, item.di_typ, item.path)
        pq.task_done()


def main(top_lvl_dirs, num_worker_threads):
    dir_queue = Queue()
    path_queue = Queue()

    # start the dir_worker threads (1 or more)
    for i in range(num_worker_threads):
        t = Thread(target=dir_worker, args=(i + 1, dir_queue, path_queue))
        t.daemon = True
        t.start()

    # start the path_worker thread (only 1)
    t = Thread(target=path_worker, args=(path_queue, ))
    t.daemon = True
    t.start()

    # add the top level directory to the dir_queue
    for i, top_lvl_dir in enumerate(top_lvl_dirs):
        dir_queue.put(DirItm(i, 0, 'D', top_lvl_dir))

    # print "waiting for directory to be scanned..."
    dir_queue.join()
    # print "waiting for paths to be saved..."
    path_queue.join()
    # print "done !!!"


if __name__ == '__main__':
    dirs_to_scan = [
        '/Users/gskluzacek/Documents/ansbl_prj',
        '/Users/gskluzacek/Documents/cr6-contents'
    ]
    wrkr_threads = 10
    main(dirs_to_scan, wrkr_threads)
