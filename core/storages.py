import os
import boto3
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from botocore.exceptions import ClientError


class LocalCacheS3FallbackStorage(FileSystemStorage):
    """
    Storage híbrido:
    - Salva os arquivos tanto localmente quanto no S3.
    - Lê primeiro do cache local; se não existir, baixa automaticamente do S3.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME

    # -------------------------------------
    # 🧱 AUXILIARES
    # -------------------------------------
    def _ensure_local_dir(self, name):
        """Cria automaticamente a pasta local, se não existir."""
        local_dir = os.path.join(settings.MEDIA_ROOT, os.path.dirname(name))
        os.makedirs(local_dir, exist_ok=True)

    def _s3_key(self, name):
        """Gera a chave completa do S3."""
        return f"media/{name}"

    # -------------------------------------
    # 💾 SALVAR (UPLOAD)
    # -------------------------------------
    def _save(self, name, content):
        """
        Sobrescreve o método padrão:
        1️⃣ Salva localmente.
        2️⃣ Envia o mesmo arquivo para o S3.
        """
        self._ensure_local_dir(name)

        # 1. Salva localmente
        saved_name = super()._save(name, content)
        local_path = os.path.join(settings.MEDIA_ROOT, saved_name)

        # 2. Faz upload para o S3
        key = self._s3_key(saved_name)
        try:
            self.s3.upload_file(local_path, self.bucket, key)
            print(f"☁️ Upload para S3 concluído: {key}")
        except Exception as e:
            print(f"❌ Erro ao enviar {key} para o S3: {e}")

        return saved_name

    # -------------------------------------
    # 📥 LEITURA (DOWNLOAD)
    # -------------------------------------
    def _download_from_s3(self, name):
        """Tenta baixar o arquivo do S3 para o cache local."""
        key = self._s3_key(name)
        local_path = os.path.join(settings.MEDIA_ROOT, name)
        self._ensure_local_dir(name)

        try:
            self.s3.download_file(self.bucket, key, local_path)
            print(f"⬇️ Cache atualizado automaticamente: {key}")
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                print(f"⚠️ Arquivo não encontrado no S3: {key}")
            else:
                print(f"❌ Erro ao baixar {key}: {e}")
            return False

    def exists(self, name):
        """Verifica se existe localmente, senão tenta baixar do S3."""
        if super().exists(name):
            return True
        return self._download_from_s3(name)

    def url(self, name):
        """
        Sempre retorna a URL local (/media/...), 
        garantindo que o site funcione mesmo se o S3 estiver offline.
        """
        return f"/media/{name}"

