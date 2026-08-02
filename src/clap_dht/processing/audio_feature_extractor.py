import io
import torch
import subprocess
import json
import torchaudio
import numpy as np
from clap_dht.utils import logger
from concurrent.futures import ThreadPoolExecutor, as_completed

CLAP_MODEL = "laion/clap-htsat-fused"
CLAP_SAMPLING_RATE = 48000
FINGER_PRINT_SIZE = 120
MAX_WORKER = 8

class AudioFeatureExtractor:
    def __init__(self, batch_size=8):
        import transformers
        transformers.logging.set_verbosity_error()
        from transformers import ClapAudioModelWithProjection, ClapProcessor
        self.batch_size = batch_size

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.processor = ClapProcessor.from_pretrained(CLAP_MODEL, local_files_only=True)
        self.model = ClapAudioModelWithProjection.from_pretrained(CLAP_MODEL, local_files_only=True).to(self.device)
        self.model.eval()
        
    def process_batch(self, batch, subpaths):
        fingerprints = []
        audio_arrays = []

        with ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
            futures = {}

            for audio_bytes in batch:
                futures[executor.submit(self.fpcalc, audio_bytes)] = self.fpcalc
                futures[executor.submit(self.resample, audio_bytes)] = self.resample

            for future, subpath in zip(as_completed(futures), subpaths):
                type = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    logger.error(f"Error: '{subpath}'")
                    logger.error(exc)
                    result = np.array([])

                if type == self.fpcalc:
                    fingerprints.append(result)
                elif type == self.resample:
                    audio_arrays.append(result)

        embeddings = self.clap(audio_arrays)

        return zip(fingerprints, embeddings)


    def fpcalc(self, audio_bytes):
        logger.debug("fpcalc start")
        result = subprocess.run(
            ["fpcalc", "-json", "-raw", "-length", f"{FINGER_PRINT_SIZE}", "-"],
            input=audio_bytes,
            capture_output=True,
            check=True,
        )

        fpdata = json.loads(result.stdout)
        fingerprint = np.array(fpdata["fingerprint"], dtype=np.uint32).tobytes()
        logger.debug("fpcalc end")
        return fingerprint

    def resample(self, audio_bytes):
        logger.debug("resample start")
        buffer = io.BytesIO(audio_bytes)
        waveform, original_sr = torchaudio.load(buffer)
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        if original_sr != CLAP_SAMPLING_RATE:
            resampler = torchaudio.transforms.Resample(orig_freq=original_sr, new_freq=CLAP_SAMPLING_RATE)
            waveform = resampler(waveform)

        audio_array = waveform.squeeze(0).numpy()
        logger.debug("resample end")
        return audio_array

    def clap(self, audio_arrays):
        logger.debug("clap_processor start")
        embeddings = []
        inputs = self.processor(
            audio=audio_arrays,
            sampling_rate=CLAP_SAMPLING_RATE,
            return_tensors="pt"
        )
        logger.debug("clap_processor end")
        inputs.to(self.device)
        logger.debug("clap_embedding start")
        with torch.no_grad():
            outputs = self.model(**inputs)
            result = outputs.audio_embeds.detach().cpu().numpy()
            for r in result:
                embeddings.append(r)
        logger.debug("clap_embedding end")
        return embeddings