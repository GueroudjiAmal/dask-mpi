import sys

from mpi4py import MPI
from tornado.ioloop import IOLoop

from dask_mpi.common import (get_host_from_interface, get_worker_name_from_mpi_rank,
                             start_scheduler, start_scheduler_loop,
                             start_worker, start_worker_loop)

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
loop = IOLoop()


def initialize(scheduler_file='scheduler.json', interface=None, nthreads=1,
               local_directory='', memory_limit='auto', nanny=False,
               bokeh=True, bokeh_port=8787, bokeh_prefix=None, bokeh_worker_port=8789):
    host = get_host_from_interface(interface)

    if rank == 0:
        scheduler = start_scheduler(loop, host=host, scheduler_file=scheduler_file,
                                    bokeh=bokeh, bokeh_port=bokeh_port, bokeh_prefix=bokeh_prefix)
        start_scheduler_loop(scheduler)
        sys.exit()

    elif rank == 1:
        pass

    else:
        name = get_worker_name_from_mpi_rank(rank)
        worker, addr = start_worker(loop, host=host, name=name, scheduler_file=scheduler_file, nanny=nanny,
                                    local_directory=local_directory, nthreads=nthreads, memory_limit=memory_limit,
                                    bokeh=bokeh, bokeh_port=bokeh_worker_port)
        start_worker_loop(worker, addr)
        sys.exit()
