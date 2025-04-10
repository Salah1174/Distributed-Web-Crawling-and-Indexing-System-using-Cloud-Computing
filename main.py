from mpi4py import MPI
import sys

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if rank == 0:
    import master_node
    master_node.master_process()
elif rank == size - 1:
    import indexer_node
    indexer_node.indexer_process()
else:
    import crawler_node
    crawler_node.crawler_process()
