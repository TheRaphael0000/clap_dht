import io
import numpy as np
from transformers import ClapAudioModelWithProjection, ClapProcessor
import transformers

transformers.logging.set_verbosity_error()

class EmbeddingModel:
    def __init__(self):
        self.model_id = "laion/clap-htsat-fused"
        self.processor = ClapProcessor.from_pretrained(self.model_id, local_files_only=True)
        self.model = ClapAudioModelWithProjection.from_pretrained(self.model_id, local_files_only=True)
        self.model.eval()

    def compute_embedding(self, filepath):
        inputs = self.processor(
            audio=[filepath],
            sampling_rate=48000,
            return_tensors="pt",
        )
        outputs = self.model(**inputs)
        embedding = outputs.audio_embeds.detach().numpy()[0]
        return embedding

    def compute_embeddings(self, filepaths):
        inputs = self.processor(
            audio=filepaths,
            sampling_rate=48000,
            return_tensors="pt",
        )
        outputs = self.model(**inputs)
        embedding = outputs.audio_embeds.detach().numpy()
        return embedding


    def serialize_embedding(embedding):
        buffer = io.BytesIO()
        np.save(buffer, embedding, allow_pickle=False)
        serialized_embedding = buffer.getvalue()
        return serialized_embedding


    def deserialize_embedding(serialized_embedding):
        buffer = io.BytesIO(serialized_embedding)
        return np.load(buffer, allow_pickle=False)
