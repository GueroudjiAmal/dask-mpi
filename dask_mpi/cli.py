import click

import asyncio
import sys

import dask
from dask.distributed import Client, Scheduler, Worker, Nanny
from distributed.cli.utils import check_python_3

from mpi4py import MPI

@click.command()
@click.option(
    "--scheduler-file",
    type=str,
    default="scheduler.json",
    help="Filename to JSON encoded scheduler information.",
)
@click.option(
    "--scheduler-port",
    default=0,
    type=int,
    help="Specify scheduler port number.  Defaults to random.",
)
@click.option(
    "--interface", type=str, default=None, help="Network interface like 'eth0' or 'ib0'"
)
@click.option(
    "--protocol", type=str, default="tcp", help="Network protocol to use like TCP"
)
@click.option("--nthreads", type=int, default=0, help="Number of threads per worker.")
@click.option(
    "--memory-limit",
    default="auto",
    help="Number of bytes before spilling data to disk. "
    "This can be an integer (nbytes) "
    "float (fraction of total memory) "
    "or 'auto'",
)
@click.option(
    "--local-directory", default="", type=str, help="Directory to place worker files"
)
@click.option(
    "--scheduler/--no-scheduler",
    default=True,
    help=(
        "Whether or not to include a scheduler. "
        "Use --no-scheduler to increase an existing dask cluster"
    ),
)
@click.option(
    "--nanny/--no-nanny",
    default=True,
    help="Start workers in nanny process for management",
)
@click.option(
    "--dashboard-address",
    type=str,
    default=":8787",
    help="Address for visual diagnostics dashboard",
)
def main(
    scheduler_file,
    interface,
    nthreads,
    local_directory,
    memory_limit,
    scheduler,
    dashboard_address,
    nanny,
    scheduler_port,
    protocol,
):

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    if rank == 0 and scheduler:

        async def run_scheduler():
            async with Scheduler(
                interface=interface,
                protocol=protocol,
                dashboard_address=dashboard_address,
            ) as scheduler:
                comm.bcast(scheduler.address, root=0)
                comm.Barrier()
                await scheduler.finished()

        asyncio.get_event_loop().run_until_complete(run_scheduler())
        sys.exit()

    else:
        scheduler_address = comm.bcast(None, root=0)
        dask.config.set(scheduler_address=scheduler_address)
        comm.Barrier()

        async def run_worker():
            WorkerType = Nanny if nanny else Worker
            async with WorkerType(
                interface=interface,
                protocol=protocol,
                nthreads=nthreads,
                memory_limit=memory_limit,
                local_directory=local_directory,
                name=rank,
            ) as worker:
                await worker.finished()

        asyncio.get_event_loop().run_until_complete(run_worker())
        sys.exit()

def go():
    check_python_3()
    main()


if __name__ == "__main__":
    go()
