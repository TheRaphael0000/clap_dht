import torch
import subprocess
import json
import numpy as np
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
import base64

from tinytag import TinyTag
import transformers
from transformers import ClapAudioModelWithProjection, ClapProcessor

from clap_dht.utils import Timer
from clap_dht.utils.consts import CLAP_MODEL, CLAP_SAMPLING_RATE, MAX_AUDIO_SECONDS

transformers.logging.set_verbosity_error()
logger = logging.getLogger("UPDATER")


def threadpool_pipeline(func, batch, subpaths, max_workers):
    output = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for audio_bytes, subpath in zip(batch, subpaths):
            futures[executor.submit(func, audio_bytes)] = subpath
        for future in as_completed(futures):
            subpath = futures[future]
            try:
                result = future.result()
            except Exception as e:
                logger.error(f"Can't '{func.__name__}': '{subpath}' \n{e}")
                result = None
            output[subpath] = result
    return [output[subpath] for subpath in subpaths]


def fingerprint_in_tags(audio_bytes):
    bytes_io = io.BytesIO(initial_bytes=audio_bytes)
    tags = TinyTag.get(file_obj=bytes_io)
    possible_keys = ["acoustid_fingerprint"]

    for pk in possible_keys:
        if pk in tags.other:
            for base64_value in tags.other[pk]:
                if base64_value is None:
                    continue
                return base64_value
    return None

def fingerprint_with_fpcalc(audio_bytes):
    result = subprocess.run(
        # use the same args as picard:
        # https://github.com/metabrainz/picard/blob/5a35d3bbde0175558bb2f441fcd952d7f18f4798/picard/acoustid/__init__.py#L285
        ["fpcalc", "-json", "-length", "120", "-"],
        input=audio_bytes,
        capture_output=True,
        check=True,
    )
    fpdata = json.loads(result.stdout)
    fingerprint_base64 = fpdata["fingerprint"]
    return fingerprint_base64


def fingerprint_to_bytes(base64_value):
    missing_padding = len(base64_value) % 4
    if missing_padding:
        base64_value += "=" * (4 - missing_padding)
    binary_value = base64.urlsafe_b64decode(base64_value)
    return binary_value


def resample_with_ffmpeg(audio_bytes):
    result = subprocess.run([
            "ffmpeg",
            "-threads", "1",
            "-i", "pipe:0",
            "-map", "0:a:0",
            "-ac", "1",
            "-ar", str(CLAP_SAMPLING_RATE),
            "-t", str(MAX_AUDIO_SECONDS),
            "-f", "f32le",
            "-acodec", "pcm_f32le",
            # "-v", "quiet",
            "pipe:1"
        ],
        input=audio_bytes,
        capture_output=True,
        check=True
    )
    logger.debug(result.stderr.decode("utf8"))
    audio_array = np.frombuffer(result.stdout, dtype=np.float32)
    array_copy = audio_array.copy()
    if len(array_copy) <= 0:
        raise Exception("ffmpeg returned an empty output")
    return array_copy


class AudioFeatureExtractor:
    def __init__(self, max_workers, ignore_existing_fingerprint, use_dht):

        self.max_workers = max_workers
        self.ignore_existing_fingerprint = ignore_existing_fingerprint
        logger.debug(f"max_workers: {self.max_workers}")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.debug(f"Embedding Projection Device: {self.device}")

        logger.debug("loading clap model...")
        self.processor = ClapProcessor.from_pretrained(CLAP_MODEL, local_files_only=True)
        self.model = ClapAudioModelWithProjection.from_pretrained(CLAP_MODEL, local_files_only=True).to(self.device)
        logger.debug("clap model loaded")
        self.model.eval()
        
    def process_batch(self, batch, subpaths):
        logger.debug("process batch start")

        with Timer("batch fingerprint"):
            fingerprints = threadpool_pipeline(self.fingerprint, batch, subpaths, self.max_workers)

        with Timer("batch resample"):
            audio_arrays = threadpool_pipeline(self.resample, batch, subpaths, self.max_workers)

        with Timer("batch clap"):
            embeddings = self.clap(audio_arrays)

        output = list(zip(fingerprints, embeddings))
        
        logger.debug(f"process batch end {len(output)}")
        return output

    def resample(self, audio_bytes):
        with Timer("resample"):
            return resample_with_ffmpeg(audio_bytes)

    def fingerprint(self, audio_bytes):
        with Timer("fingerprint"):
            if not self.ignore_existing_fingerprint:
                filetag_fingerprint = fingerprint_in_tags(audio_bytes)
                if filetag_fingerprint:
                    return fingerprint_to_bytes(filetag_fingerprint)

            fpcalc_fingerprint = fingerprint_with_fpcalc(audio_bytes)

            return fingerprint_to_bytes(fpcalc_fingerprint)
        return None

    def clap(self, audio_arrays):
        valid_indices = [i for i, a in enumerate(audio_arrays) if a is not None]
        valid_audio_arrays = [audio_arrays[i] for i in valid_indices]
        if len(valid_audio_arrays) <= 0:
            return [None] * len(audio_arrays)
        embeddings = []
        with Timer("clap processor"):
            inputs = self.processor(
                audio=valid_audio_arrays,
                sampling_rate=CLAP_SAMPLING_RATE,
                return_tensors="pt"
            )
        with Timer("clap projection"):
            inputs = inputs.to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
                result = outputs.audio_embeds.detach().cpu().numpy()
                for r in result:
                    embeddings.append(r)
        valid_embeddings = [embeddings[i] if i in valid_indices else None for i in range(len(audio_arrays))]
        return valid_embeddings