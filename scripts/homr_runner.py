"""Version-specific HOMR 0.7 adapter. Only this process imports the engine.
Keeps model artifacts in the user data folder without modifying HOMR source.
"""

# ruff: noqa: E402
# Native thread limits must be set before importing ONNX/HOMR.
import hashlib
import json
import os
import sys
from pathlib import Path

MODELS = Path(os.environ.get("NOTEPILOT_DATA_DIR", Path(__file__).resolve().parents[1] / "data")) / "models"
MODELS.mkdir(parents=True, exist_ok=True)
# ORT defaults to available cores. Bound native worker pools on ordinary PCs.
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
if os.name != "nt" and "--status" not in sys.argv:
    import resource

    resource.setrlimit(resource.RLIMIT_CPU, (1200, 1205))
    # Do not cap virtual address space: ONNX reserves large arenas even for small physical allocations.

import homr.main as main
import homr.segmentation.config as segmentation
import homr.segmentation.inference_segnet as inference
import homr.transformer.configs as transformer
import onnxruntime as ort
from homr.transformer.configs import default_config


class BoundedCpuSession(ort.InferenceSession):
    def __init__(self, path_or_bytes, sess_options=None, providers=None, **kwargs):
        if sess_options is None:
            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = max(1, min(4, os.cpu_count() or 1))
            sess_options.inter_op_num_threads = 1
        super().__init__(path_or_bytes, sess_options=sess_options, providers=providers, **kwargs)


ort.InferenceSession = BoundedCpuSession


class LocalModelPaths(transformer.FilePaths):
    def __init__(self):
        super().__init__()
        for name in ("encoder_path", "decoder_path", "encoder_path_fp16", "decoder_path_fp16"):
            setattr(self, name, str(MODELS / Path(getattr(self, name)).name))


transformer.FilePaths = LocalModelPaths

for field in ("segnet_path_onnx", "segnet_path_onnx_fp16"):
    path = str(MODELS / Path(getattr(segmentation, field)).name)
    setattr(segmentation, field, path)
    setattr(main, field, path)
    setattr(inference, field, path)
for field in ("encoder_path", "decoder_path", "encoder_path_fp16", "decoder_path_fp16"):
    setattr(
        default_config.filepaths, field, str(MODELS / Path(getattr(default_config.filepaths, field)).name)
    )

paths = [
    segmentation.segnet_path_onnx,
    default_config.filepaths.encoder_path,
    default_config.filepaths.decoder_path,
]
checksums = {}
try:
    manifest = json.loads((MODELS / "manifest.json").read_text(encoding="utf-8"))
    checksums = {m["name"]: m["sha256"] for m in manifest["artifacts"]}
except (OSError, ValueError, KeyError, TypeError):
    pass
verified = all(
    Path(p).is_file()
    and checksums.get(Path(p).name) == hashlib.file_digest(Path(p).open("rb"), "sha256").hexdigest()
    for p in paths
)

if "--status" in sys.argv:
    print(
        json.dumps(
            dict(
                version="0.7.0",
                mode="CPU",
                installed=True,
                ready=verified,
                message="Lokale Modellintegrität geprüft."
                if verified
                else "Gewichte fehlen oder sind verändert. Bitte die KI-Einrichtung ausführen.",
                models=[
                    dict(
                        name=Path(p).name,
                        present=Path(p).is_file(),
                        bytes=Path(p).stat().st_size if Path(p).is_file() else 0,
                    )
                    for p in paths
                ],
            )
        )
    )
else:
    if "--init" not in sys.argv:
        if not verified:
            raise RuntimeError(
                "Modellgewichte fehlen oder ihre lokale Prüfsumme stimmt nicht. Bitte die KI-Einrichtung ausführen."
            )
        # Recognition never needs networking once initialized. Fail instead of silently downloading.
        import urllib.request

        import requests

        def offline_request(*args, **kwargs):
            raise RuntimeError(
                "Offline-Erkennung: eine Modelldatei fehlt. Bitte die KI-Einrichtung erneut ausführen."
            )

        requests.sessions.Session.request = offline_request
        urllib.request.urlopen = offline_request
    # CPU is the predictable baseline. Optional GPU is a separate, documented engine setup.
    sys.argv.extend(["--gpu", "no"])
    main.main()
