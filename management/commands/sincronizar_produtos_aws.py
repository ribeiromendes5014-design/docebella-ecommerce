# produtos/management/commands/sincronizar_produtos_aws.py
from django.core.management.base import BaseCommand
from produtos.models import Produto
from produtos.models_cache import ProdutoCache
from django.utils import timezone
import hashlib
import json

class Command(BaseCommand):
    help = "Sincroniza os produtos da AWS para o cache local"

    def handle(self, *args, **options):
        produtos = Produto.objects.all()
        atualizados = 0
        criados = 0

        for p in produtos:
            # Cria um hash simples com base nos dados relevantes
            conteudo = json.dumps({
                'id': p.id,
                'nome': p.nome,
                'preco': str(p.preco),
                'descricao': p.descricao,
                'atualizado_em': str(p.atualizado_em),
            }, sort_keys=True)
            hash_conteudo = hashlib.md5(conteudo.encode()).hexdigest()

            cache, criado = ProdutoCache.objects.get_or_create(produto_id=p.id)
            if cache.hash_conteudo != hash_conteudo or criado:
                cache.nome = p.nome
                cache.preco = p.preco
                cache.dados_json = json.loads(conteudo)
                cache.hash_conteudo = hash_conteudo
                cache.atualizado_em = timezone.now()
                cache.save()
                if criado:
                    criados += 1
                else:
                    atualizados += 1

        self.stdout.write(self.style.SUCCESS(f"✅ {criados} novos produtos adicionados ao cache."))
        self.stdout.write(self.style.SUCCESS(f"♻️ {atualizados} produtos atualizados no cache."))
        self.stdout.write(self.style.SUCCESS("Sincronização concluída com sucesso."))
