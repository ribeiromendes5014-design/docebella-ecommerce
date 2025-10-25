from django.db import connection

print("🔧 Corrigindo tabela 'carrinho_itemcarrinho'...")

with connection.cursor() as cursor:
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'carrinho_itemcarrinho'
                AND column_name = 'preco'
            ) THEN
                ALTER TABLE carrinho_itemcarrinho
                ADD COLUMN preco NUMERIC(10,2) DEFAULT 0;
                RAISE NOTICE '✅ Coluna preco adicionada com sucesso!';
            ELSE
                RAISE NOTICE '⚠️  Coluna preco já existe. Nenhuma alteração feita.';
            END IF;
        END$$;
    """)

print("✅ Operação concluída com sucesso.")
