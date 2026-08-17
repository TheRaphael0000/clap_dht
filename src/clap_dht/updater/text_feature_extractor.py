import logging

import torch
import transformers
from transformers import AutoTokenizer, ClapTextModelWithProjection
from torch.utils.data import DataLoader, IterableDataset

from clap_dht.utils import Timer
from clap_dht.utils.consts import CLAP_MODEL, CLAP_PROCESSOR

transformers.logging.set_verbosity_error()
logger = logging.getLogger("UPDATER")

class TextFeatureExtractor:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.debug(f"Embedding Projection Device: {self.device}")
        self.tokenizer = AutoTokenizer.from_pretrained(CLAP_PROCESSOR)
        self.model = ClapTextModelWithProjection.from_pretrained(CLAP_MODEL).to(self.device)
        self.model.eval()

    def clap(self, texts):
        with Timer("tokenizer"):
            inputs = self.tokenizer(
                texts, 
                padding=True, 
                return_tensors="pt"
            )

        embeddings = []
        with Timer("clap projection"):
            inputs = inputs.to(self.device)
            outputs = self.model(**inputs)
            result = outputs.text_embeds.detach().cpu().numpy()
            for r in result:
                embeddings.append(r)
        return embeddings

class GenreDataset(IterableDataset):
    def __init__(self):
        pass

    def __iter__(self):
        with open("src/clap_dht/utils/musicbrainz_genres.txt", "r") as f:
            for row in f:
                yield row.replace("\n", "")


if __name__ == "__main__":
    te = TextFeatureExtractor()
    from scipy.spatial.distance import pdist, squareform
    import itertools
    import pandas as pd


    ds = GenreDataset()
    dl = DataLoader(ds, batch_size=128)

    embeddings = []
    labels = []
    for i, b in enumerate(dl):
        print(f"Batch {i}")
        labels.extend(b)
        embeddings.extend(te.clap(b))

    print("distance")


    dist_matrix = squareform(pdist(embeddings, metric='cosine'))

    df = pd.DataFrame(dist_matrix, index=labels, columns=labels)

    print(df["pop"].sort_values())
    # df.to_html("distance_matrix.html", float_format=lambda x: f"{x:.3f}")

    # print(df)