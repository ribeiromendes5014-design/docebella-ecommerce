import os
from django.core.files.storage import FileSystemStorage
from django.conf import settings

class LocalCacheS3FallbackStorage(FileSystemStorage):
    """
    Storage híbrido:
    - Lê primeiro do cache local (MEDIA_ROOT)
    - Se o arquivo não existir, gera URL pública do S3
    """

    def url(self, name):
        local_path = os.path.join(settings.MEDIA_ROOT, name)
        if os.path.exists(local_path):
            # ✅ Serve o arquivo local (cache)
            return settings.MEDIA_URL + name
        else:
            # ☁️ Fallback: gera URL do S3
            return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/media/{name}"
