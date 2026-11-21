"""Batched SigLIP image embeddings and exhaustive cosine similarity search."""

from collections import defaultdict
import io

from PIL import Image, ImageOps


class SiglipSearch:
    def __init__(self, model_path, revision, device, batch_size, threshold):
        import torch
        from transformers import AutoConfig, AutoModel, Siglip2ImageProcessorPil, SiglipImageProcessorPil

        self.torch = torch
        self.device = torch.device(
            ("cuda" if torch.cuda.is_available() else "cpu") if device == "auto" else device
        )
        self.batch_size = batch_size
        self.threshold = threshold
        config = AutoConfig.from_pretrained(model_path, revision=revision, local_files_only=True)
        processors = {"siglip": SiglipImageProcessorPil, "siglip2": Siglip2ImageProcessorPil}
        if config.model_type not in processors:
            raise ValueError(f"Expected a SigLIP model, got {config.model_type}")
        self.processor = processors[config.model_type].from_pretrained(
            model_path, revision=revision, local_files_only=True
        )
        self.model = AutoModel.from_pretrained(
            model_path, config=config, revision=revision, local_files_only=True
        ).to(self.device).eval()
        self.revision = getattr(self.model.config, "_commit_hash", None) or revision
        self.model_path = model_path
        self.references = defaultdict(set)
        self.pending = []
        self.vectors = {}

    def embed(self, blobs):
        images = []
        for blob in blobs:
            with Image.open(io.BytesIO(blob)) as original:
                images.append(ImageOps.exif_transpose(original).convert("RGB"))
        inputs = self.processor(images=images, return_tensors="pt")
        with self.torch.inference_mode():
            features = self.model.get_image_features(
                **{k: v.to(self.device) for k, v in inputs.items()}
            )
            # Transformers versions differ in whether they return a tensor or a model output.
            if not self.torch.is_tensor(features):
                features = features.pooler_output
            features = features.float()
            if features.ndim != 2 or features.shape[0] != len(images):
                raise ValueError("SigLIP returned an unexpected embedding shape")
            norms = self.torch.linalg.vector_norm(features, dim=1)
            if not self.torch.isfinite(norms).all() or (norms == 0).any():
                raise ValueError("SigLIP returned an invalid image embedding")
            return (features / norms[:, None]).cpu()

    def add(self, key, pixel_hash, blob):
        if pixel_hash not in self.references:
            self.pending.append((pixel_hash, blob))
        self.references[pixel_hash].add(key)
        if len(self.pending) == self.batch_size:
            self.flush()

    def flush(self):
        if self.pending:
            vectors = self.embed([blob for _, blob in self.pending])
            self.vectors.update((key, vector) for (key, _), vector in zip(self.pending, vectors))
            self.pending.clear()

    def finish(self):
        self.flush()
        self.keys = list(self.vectors)
        if not self.keys:
            raise ValueError("No benchmark embeddings for SigLIP")
        self.matrix = self.torch.stack([self.vectors[key] for key in self.keys])
        self.vectors.clear()
        print(f"SigLIP: indexed {len(self.keys)} unique benchmark images", flush=True)

    def find(self, images):
        """Return a hit list per query image. Keep every match above the threshold."""
        if not images:
            return []
        query = self.embed(images)
        # Chunk the reference matrix to avoid putting the whole index on the GPU.
        hits = [[] for _ in images]
        query = query.to(self.device)
        with self.torch.inference_mode():
            for start in range(0, len(self.keys), 4096):
                scores = query @ self.matrix[start:start + 4096].to(self.device).T
                pairs = (scores >= self.threshold).nonzero(as_tuple=False)
                values = scores[pairs[:, 0], pairs[:, 1]].tolist()
                for (q, ref), score in zip(pairs.tolist(), values):
                    image_hash = self.keys[start + ref]
                    hits[q].extend((key, "image_siglip_cosine", round(score, 6))
                                   for key in self.references[image_hash])
        return hits
