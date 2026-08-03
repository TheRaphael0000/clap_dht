import io
import torch
import subprocess
import json
import torchaudio
import numpy as np
import logging

from concurrent.futures import ThreadPoolExecutor, as_completed
from clap_dht.utils import Timer

logger = logging.getLogger()
CLAP_MODEL = "laion/clap-htsat-fused"
CLAP_SAMPLING_RATE = 48000
FINGER_PRINT_SIZE = 120
MAX_WORKER = 8
MAX_AUDIO_SECONDS = 60

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
            except subprocess.CalledProcessError as e:
                logger.error(f"Can't process: '{subpath}' \n{e}")
                result = None
            output[subpath] = result
    return [output[subpath] for subpath in subpaths]


class AudioFeatureExtractor:
    def __init__(self, max_workers):
        import transformers
        transformers.logging.set_verbosity_error()
        from transformers import ClapAudioModelWithProjection, ClapProcessor
        self.max_workers = max_workers
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

        with Timer("batch resample"):
            audio_arrays = threadpool_pipeline(self.resample, batch, subpaths, self.max_workers)

        with Timer("batch clap"):
            embeddings = self.clap(audio_arrays)

        with Timer("batch fingerprint"):
            fingerprints = threadpool_pipeline(self.fingerprint, batch, subpaths, self.max_workers)

        output = list(zip(fingerprints, embeddings))
        
        logger.debug(f"process batch end {len(output)}")
        return output


    def fingerprint(self, audio_bytes):
        with Timer("fingerprint"):
            result = subprocess.run(
                ["fpcalc", "-json", "-raw", "-length", f"{FINGER_PRINT_SIZE}", "-"],
                input=audio_bytes,
                capture_output=True,
                check=True,
            )

            fpdata = json.loads(result.stdout)
            fingerprint = np.array(fpdata["fingerprint"], dtype=np.uint32).tobytes()
        return fingerprint

    def resample(self, audio_bytes):
        with Timer("resample"):
            cmd = [
                "ffmpeg",
                "-threads", "1",
                "-i", "pipe:0",
                "-ac", "1",
                "-ar", str(CLAP_SAMPLING_RATE),
                "-t", str(MAX_AUDIO_SECONDS),
                "-f", "f32le",
                "-acodec", "pcm_f32le",
                "-v", "quiet",
                "pipe:1"
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    input=audio_bytes,
                    capture_output=True,
                    check=True
                )
                
                audio_array = np.frombuffer(result.stdout, dtype=np.float32)
                
                return audio_array.copy()
                
            except subprocess.CalledProcessError as e:
                logger.error(f"FFmpeg decoding failed: {e.stderr or 'Unknown error'}")
                return None

    def clap(self, audio_arrays):
        with Timer("clap processor"):
            embeddings = []
            inputs = self.processor(
                audio=audio_arrays,
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
        return embeddings