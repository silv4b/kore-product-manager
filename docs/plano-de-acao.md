<!-- markdownlint-disable MD036 MD060 -->

# Plano de Ação - Kore Product Manager

> Data: 2026-05-15
> Objetivo: Analisar qualidade de código, fluxo entre funcionalidades e qualidade dos testes, e elaborar plano para deixar o projeto minimamente pronto para deploy.

---

## Situação Atual

| Aspecto | Status |
|---------|--------|
| Quebras de fluxo (crash em produção) | **3 resolvidas** ✅ |
| Qualidade de código | Média - 5 críticos, 5 altos, 7 médios |
| Testes - Cobertura real | ~35% (Products 65%, API 0%, Partners 0%) |
| Testes - Qualidade | Integração excelente, unitários bons, API/Partners zerados |

---

## Fase 1 - Correções Críticas ✅ CONCLUÍDA

### 1.1 Missing `__init__.py` em `partners/templatetags/` ✅ CORRIGIDO

- **Problema**: Django não descobre `partner_masks` → `TemplateSyntaxError` ao carregar páginas de clientes/fornecedores
- **Arquivo**: `partners/templatetags/__init__.py` (criar)
- **Impacto**: Crash 500 ao acessar `/partners/clientes/` ou `/partners/fornecedores/`
- **Solução**: Criado `partners/templatetags/__init__.py`

### 1.2 `product_movement_view` crasha em usuário anônimo ✅ CORRIGIDO

- **Problema**: Acessa `request.user.profile` sem `@login_required` → `AttributeError`
- **Arquivo**: `products/views.py:492-493`
- **Impacto**: Crash 500 ao acessar movimento de produto público sem estar logado
- **Solução**: Adicionar guarda `is_authenticated` + fallback para session (preserva visualização pública)

### 1.3 ~~`set_view_mode` crasha em usuário anônimo~~ ✅ FALSO POSITIVO

- **Problema**: Análise inicial apontou crash, mas o código já tem guarda `is_authenticated` (linha 1019) antes de acessar `profile` (linha 1020). Não há crash.
- **Arquivo**: `products/views.py:1017-1028`
- **Status**: Nenhuma ação necessária.

### 1.4 `SECRET_KEY` hardcoded em `settings.py` ✅ CORRIGIDO

- **Problema**: Chave secreta no repositório público
- **Arquivo**: `kore-product-manager/settings.py:16`
- **Impacto**: Segurança comprometida em produção
- **Solução**: Movido para `os.getenv("SECRET_KEY")` com fallback dev

### 1.5 `ALLOWED_HOSTS = ["*"]` ✅ CORRIGIDO

- **Problema**: Aceita requisições de qualquer host em produção
- **Arquivo**: `kore-product-manager/settings.py:22`
- **Impacto**: Vulnerabilidade de Host Header Injection
- **Solução**: Agora lê de `os.getenv("ALLOWED_HOSTS", "*").split(",")`

### 1.6 Configuração de cobertura testando arquivos errados ✅ CORRIGIDO

- **Problema**: `--cov=products/tests/` mede cobertura dos testes, não do código fonte
- **Arquivo**: `pytest.ini:11`
- **Impacto**: Relatório de cobertura enganoso (mostra 100% para código não testa## Fase 2 - Correções de Fluxo e Integridade ✅ CONCLUÍDA

### 2.1 `AUTHENTICATION_BACKENDS` definido duas vezes ✅

- **Problema**: Linhas 63 e 196 em `settings.py`; segunda sobrescreve primeira
- **Arquivo**: `kore-product-manager/settings.py:63,196`
- **Impacto**: Código morto e confusão, mas sem impacto funcional (valores idênticos)
- **Solução**: Remover bloco duplicado da linha 63

### 2.2 `api/serializers.py` - categoria de outro usuário via API ✅

- **Problema**: `queryset=Category.objects.all()` permite associar categorias de outros usuários
- **Arquivo**: `api/serializers.py:47`
- **Impacto**: Vazamento de dados e violação de isolamento entre usuários
- **Solução**: Sobrescrever `__init__` do serializer para filtrar `category_ids` pelo `request.user`

### 2.3 Conflito `dotenv` vs `python-dotenv` em `pyproject.toml` ✅

- **Problema**: Dependências concorrentes; pacote `dotenv` não mantido desde 2016
- **Arquivo**: `pyproject.toml:14,19`
- **Impacto**: Instalação imprevisível; pode resolver pacote errado
- **Solução**: Remover `"dotenv>=0.9.9"`, manter apenas `"python-dotenv"`

### 2.4 `assert` em produção em `products/forms.py` ✅

- **Problema**: `assert stock is not None` é removido com `-O` (modo otimizado)
- **Arquivo**: `products/forms.py:79`
- **Impacto**: Validação removida em produção com Python -O
- **Solução**: Substituir por `if stock is None: raise forms.ValidationError(...)`

### 2.5 Timezone inconsistency em `product_movement_view` e `product_movement_overview` ✅

- **Problema**: Datas não são `make_aware()` ao filtrar movimentos
- **Arquivo**: `products/views.py:467-478, 534-545`
- **Impacto**: Filtros de data incorretos (diferença de fuso horário)
- **Solução**: Aplicar `timezone.make_aware()` consistente (como já feito em `price_history_view`)

### 2.6 `user_public_catalog` computa stats em Python (memory leak potencial) ✅

- **Problema**: `sum(p.price * p.stock for p in products)` carrega tudo em memória em vez de usar o banco
- **Arquivo**: `products/views.py:870-874`
- **Impacto**: Problema de performance com muitos produtos; inconsistente com outras views que usam `ExpressionWrapper`
- **Solução**: Usar `ExpressionWrapper` + `Sum` como nas outras viewstente com outras views que usam `ExpressionWrapper`
- **Solução**: Usar `ExpressionWrapper` + `Sum` como nas outras views

---

## Fase 3 - Testes (Preencher Lacunas)

### 3.1 Implementar `api/tests.py`

- **Problema**: 10 métodos de teste VAZIOS (só docstrings, zero assertions)
- **Arquivo**: `api/tests.py:57-131`
- **Cobertura atual**: 0% da API
- **Ação**: Implementar todos os testes de API (autenticação JWT, CRUD de produtos/categorias, movimentações)

### 3.2 Implementar `partners/tests.py`

- **Problema**: Arquivo placeholder vazio (4 linhas)
- **Arquivo**: `partners/tests.py`
- **Cobertura atual**: 0% do app partners
- **Ação**: Criar testes para modelos (Customer, Supplier), formulários (CustomerForm, SupplierForm), views (CRUD de clientes e fornecedores), template tags (mask_cpf, mask_cnpj, mask_phone)

### 3.3 Remover/corrigir código quebrado em `test_utils.py`

- **Problema**: `Client()` não importado; `response` não definido; `setUp()` retorna valor
- **Arquivo**: `products/tests/test_utils.py:17-25`
- **Ação**: Remover código morto ou corrigir com import e parâmetros adequados

### 3.4 Criar `conftest.py`

- **Problema**: Sem fixtures compartilhadas; UserFactory e CategoryFactory importados manualmente em cada arquivo
- **Ação**: Criar `products/tests/conftest.py` com fixtures (auth_client, user, other_user, category, product)

### 3.5 Adicionar testes para views não cobertas

- **Arquivo**: `products/tests/test_views.py` (estender)
- **Views sem teste**:
  - `product_bulk_action` (bulk delete, make_public, make_private, add_category)
  - `product_movement_view`, `product_movement_overview`, `movement_select_product`, `perform_movement`
  - `price_history_overview` (filtros, stats, sparkline)
  - `category_delete` (GET confirm)

### 3.6 Adicionar testes para `ProductMovement` model e `track_stock_changes` signal

- **Problema**: Modelo de 20 linhas + signal de 50 linhas com lógica complexa = zero cobertura
- **Arquivo**: `products/tests/test_models.py` (estender)

### 3.7 Remover `time.sleep()` dos testes

- **Problema**: `test_price_history_ordering` usa `sleep(0.01)` — frágil em CI
- **Arquivo**: `products/tests/test_models.py:210,216`
- **Ação**: Substituir por `freezegun` ou `datetime` mock

---

## Fase 4 - Refatoração de Código (Qualidade) ✅ CONCLUÍDA

### 4.1 Extrair lógica de filtro duplicada ✅

- **Problema**: Mesmo filtro (q, category_id, min_price, max_price, min_stock, max_stock) copiado 6 vezes em `products/views.py`
- **Arquivos**: `products/views.py:78-93, 329-337, 511-518, 593-600, 844-866, 924-935`
- **Ação**: Criar `ProductFilter` usando `django-filter` (já instalado!) ou função `filter_products(queryset, request)`

### 4.2 Extrair lógica de ordenação duplicada ✅

- **Problema**: Dict `valid_sort_fields` e lógica de prefixo copiados 4 vezes
- **Arquivos**: `products/views.py:96-108, 682-703, 937-947`, `partners/views.py:27-43, 113-131`
- **Ação**: Criar função `sort_queryset(queryset, request, valid_fields, default_sort)`

### 4.3 Extrair permission check duplicado ✅

- **Problema**: `if not product.is_public: if not request.user.is_authenticated or ...` repetido 3x
- **Arquivo**: `products/views.py:258-261, 270-273, 451-454`
- **Ação**: Criar método `Product.is_accessible_by(user)` ou função helper

### 4.4 Criar `ProductManager.for_user(user)` ✅

- **Problema**: `Product.objects.filter(user=request.user)` repetido 10+ vezes
- **Arquivo**: `products/models.py`
- **Ação**: Adicionar `class ProductManager(models.Manager)` com `def for_user(self, user)` e `def public(self)`

### 4.5 Quebrar funções gigantes ✅

- `product_list` (134 linhas) — extrair filtro, ordenação, stats, view_mode
- `price_history_overview` (130 linhas) — extrair stats, sparkline, trend analysis
- **Arquivo**: `products/views.py`

### 4.6 Import cleanup ✅

- Remover imports duplicados dentro de funções (`datetime`, `Sum`)
- Remover imports não utilizados (`api/models.py`, `api/admin.py`)
- Padronizar aspas (single para double em `apps.py`)
- Remover self-import com `TYPE_CHECKING` em `products/models.py:7-8`

### 4.7 Adicionar type hints ✅

- Pelo menos views e forms (assinaturas de função)

---

## Fase 5 - Preparação para Deploy

### 5.1 Configurar ambiente de produção

- Migrar `SECRET_KEY` e `ALLOWED_HOSTS` para variáveis de ambiente
- Configurar `DEBUG=False` por env var
- Verificar `CSRF_COOKIE_HTTPONLY` (decidir se True em prod)
- Garantir que `django-cors-headers` está configurado (declarado mas não instalado no middleware)

### 5.2 Pipeline CI/CD

- Workflow GitHub Actions já existe (`release-homolog.yaml`) mas só faz build Docker
- Adicionar step de `uv sync --frozen && ruff check . && pytest --cov` antes do build
- Adicionar lint (ruff) no pipeline

### 5.3 Docker ✅ CONCLUÍDO

- `docker-compose.yml` criado na raiz com serviços `db` (postgres:14) e `app` (build local)
- `entrypoint.sh` hardcoded `postgres14` como host — resolvido pelo network do compose
- Porta do CMD no Dockerfile alinhada: `--bind 0.0.0.0:8005` (coerente com `EXPOSE 8005`)
- Healthcheck configurado no PostgreSQL para `depends_on: condition: service_healthy`
- Volume `pgdata` para persistência do banco

### 5.4 Documentação

- Atualizar `.env.example` com TODAS as variáveis necessárias (SECRET_KEY, ALLOWED_HOSTS, DEBUG)
- Verificar se README.md reflete o setup atual

---

## Estimativa de Esforço

| Fase | Itens | Esforço Estimado | Impacto |
|------|-------|-----------------|---------|
| **Fase 1** - Correções críticas | 6 | 2-3h | Elimina crashes em produção |
| **Fase 2** - Fluxo/integridade | 6 | 4-6h | Elimina bugs de dados e runtime |
| **Fase 3** - Testes | 7 | 8-12h | Cobertura de ~35% para ~70% |
| **Fase 4** - Refatoração | 7 | 12-16h | Qualidade e manutenibilidade |
| **Fase 5** - Deploy | 4 | 4-6h | Pronto para deploy real |

**Total estimado: 30-43h**

---

## Recomendação de Priorização

| Cenário | Fases | Esforço | Pronto para |
|---------|-------|---------|-------------|
| **Mínimo viável** | 1 + 2 | ~8h | Deploy sem crashes |
| **Recomendado** | 1 + 2 + 3 | ~20h | Deploy + cobertura de testes |
| **Ideal** | 1 + 2 + 3 + 4 + 5 | ~40h | Produção profissional |

**Mínimo para deploy seguro:** Corrigir os 12 itens das Fases 1 e 2 elimina todos os crashes, bugs de runtime e integridade de dados.
