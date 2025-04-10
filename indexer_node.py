from mpi4py import MPI
import time
import logging
import os
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT
from whoosh.qparser import QueryParser

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - Indexer - %(levelname)s - %(message)s')


def create_index():
    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")
    schema = Schema(content=TEXT(stored=True))
    return create_in("indexdir", schema)


def indexer_process():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    logging.info(f"Indexer node started with rank {rank} of {size}")
    ix = create_index()
    writer = ix.writer()

    while True:
        status = MPI.Status()
        content = comm.recv(source=MPI.ANY_SOURCE, tag=2, status=status)
        source_rank = status.Get_source()

        if not content:
            logging.info(f"Indexer {rank} received shutdown signal. Exiting.")
            break

        try:
            writer.add_document(content=content)
            logging.info(
                f"Indexer {rank} indexed content from Crawler {source_rank}.")
            comm.send(
                f"Indexer {rank} - Indexed content from Crawler {source_rank}", dest=0, tag=99)
        except Exception as e:
            logging.error(f"Indexer {rank} error indexing content: {e}")
            comm.send(f"Indexer {rank} - Error indexing: {e}", dest=0, tag=999)

    writer.commit()


if __name__ == '__main__':
    indexer_process()
