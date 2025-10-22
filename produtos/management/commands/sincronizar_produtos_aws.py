from django.core.management.base import BaseCommand
from produtos.models import Produto, Categoria
import boto3
import json
from django.conf import settings


class Command(BaseCommand):
    help = 'Sincroniza produtos da AWS S3 para o cache local (Render).'

    def handle(self, *args, **options):
        self.stdout.write("🔄 Iniciando sincronização de produtos da AWS...")

        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )

            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            file_key = 'media/produtos/produtos.json'
            
            print(f"Tentando baixar de S3: s3://{bucket_name}/{file_key}")

            response = s3.get_object(Bucket=bucket_name, Key=file_key)
            conteudo = response['Body'].read().decode('utf-8')
            produtos_aws = json.loads(conteudo)

            atualizados = 0
            criados = 0

            for item in produtos_aws:
                categoria_nome = item.get('categoria', 'Sem Categoria')
                categoria, _ = Categoria.objects.get_or_create(nome=categoria_nome)

                produto, created = Produto.objects.update_or_create(
                    sku=item['sku'],
                    defaults={
                        'nome': item['nome'],
                        'descricao': item.get('descricao', ''),
                        'preco': item['preco'],
                        'estoque': item['estoque'],
                        'categoria': categoria,
                        'disponivel': item.get('disponivel', True),
                    }
                )

                if created:
                    criados += 1
                else:
                    atualizados += 1

            self.stdout.write(self.style.SUCCESS(
                f"✅ Sincronização concluída! {criados} novos produtos, {atualizados} atualizados."
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao sincronizar: {e}"))
