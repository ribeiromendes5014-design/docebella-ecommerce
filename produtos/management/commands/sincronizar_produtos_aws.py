from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
import os
from datetime import datetime, timezone

class Command(BaseCommand):
    help = "Baixa imagens do S3 e mantém cache local atualizado em /media/produtos/"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Força re-download de todos os arquivos, ignorando cache local"
        )

    def handle(self, *args, **options):
        force = options["force"]

        self.stdout.write("🔄 Iniciando sincronização de imagens S3 → cache local...")

        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        bucket = settings.AWS_STORAGE_BUCKET_NAME
        prefix = "media/media/produtos/"
        local_dir = os.path.join(settings.MEDIA_ROOT, "produtos")
        print(f"📁 Baixando arquivos de: s3://{bucket}/{prefix}")
        print(f"📂 Salvando localmente em: {local_dir}")


        os.makedirs(local_dir, exist_ok=True)
        atualizados = 0
        mantidos = 0

        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

        for obj in response.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue  # pula diretórios virtuais

            filename = os.path.basename(key)
            local_path = os.path.join(local_dir, filename)

            # Se o modo --force está ativo, baixa tudo novamente
            if force:
                s3.download_file(bucket, key, local_path)
                atualizados += 1
                self.stdout.write(f"⬇️ (forçado) Atualizado: {filename}")
                continue

            # Data de modificação no S3 em UTC
            s3_time = obj["LastModified"].astimezone(timezone.utc)

            # Se o arquivo local já existe, compara timestamps
            if os.path.exists(local_path):
                local_mtime = os.path.getmtime(local_path)
                local_dt = datetime.fromtimestamp(local_mtime, tz=timezone.utc)

                if s3_time <= local_dt:
                    mantidos += 1
                    continue  # já está atualizado

            # Baixa o arquivo atualizado
            s3.download_file(bucket, key, local_path)
            atualizados += 1
            self.stdout.write(f"⬇️ Atualizado: {filename}")

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Cache sincronizado! {atualizados} arquivos baixados, {mantidos} mantidos."
            )
        )
