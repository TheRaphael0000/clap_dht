import faiss
import numpy as np

class LSHByteHasher:
    def __init__(self, dim: int, nbits: int):
        self.dim = dim
        self.nbits = nbits
        self.index = faiss.IndexLSH(dim, nbits)

    def _bytes_to_vector(self, data: bytes) -> np.ndarray:
        arr = np.frombuffer(data, dtype=np.uint8).astype(np.float32)
        if len(arr) < self.dim:
            arr = np.pad(arr, (0, self.dim - len(arr)))
        else:
            arr = arr[:self.dim]
        return np.expand_dims(arr, axis=0)

    def get_bucket_bytes(self, data: bytes) -> bytes:
        vec = self._bytes_to_vector(data)
        binary_code = self.index.sa_encode(vec)
        return binary_code.tobytes()

    
lsh = LSHByteHasher(dim=128, nbits=32)