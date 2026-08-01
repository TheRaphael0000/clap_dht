import acoustid

async def compute_fingerprint(filepath):
    duration, fingerprint = acoustid.fingerprint_file(filepath, force_fpcalc=True, maxlength=50)
    return fingerprint.decode()
