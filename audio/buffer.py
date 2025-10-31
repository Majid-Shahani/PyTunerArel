import threading
import numpy as np


class Chunk:
    def __init__(self, size, data_type=np.float32):
        self.data = np.zeros(size, data_type)
        self.lock = threading.Lock()
        self.ready = False


class RollingBuffer:
    def __init__(self, number_of_chunks, chunk_size, data_type=np.float32):
        self.chunks = [Chunk(chunk_size, data_type) for _ in range(number_of_chunks)]
        self.write_index = 0
        self.read_index = -1
        self.lock = threading.Lock()

    def write(self, data):
        with self.chunks[self.write_index].lock:
            index = self.write_index  # for readable lines
            np.copyto(self.chunks[index].data, data)
            self.chunks[index].ready = True
        with self.lock:
            self.read_index = index
            self.write_index = (index + 1) % len(self.chunks)

    def read(self) -> None | np.ndarray:
        with self.lock:
            index = self.read_index
        if index == -1:
            return None
        with self.chunks[index].lock:
            if not self.chunks[index].ready:
                return None
            out = self.chunks[index].data.copy()
        return out