# Reestruturação

Para estruturar um sistema real e robusto de controle de estoque e cadeia de suprimentos (frequentemente integrados em módulos de ERP), a modelagem de dados precisa ir além do básico para garantir consistência fiscal, rastreabilidade e inteligência de negócio.

Abaixo está o mapeamento das entidades essenciais e os dados fundamentais que cada uma deve conter, estruturados para garantir a integridade do banco de dados (relacionamentos, chaves e auditoria).

## 1. Produto (Core do Sistema)

A entidade central. Em cenários reais, um produto não é apenas nome e preço; ele carrega atributos fiscais e de controle de armazenamento.

* **Identificação:**
* `id` (UUID ou Auto-incremento)
* `codigo_barras` (EAN/GTIN) ou `sku` (Stock Keeping Unit - código interno estruturado)
* `nome`, `descricao` e `marca`

* **Classificação e Logística:**
* `categoria_id` (Chave estrangeira para a tabela de Categorias)
* `unidade_medida` (UN, KG, CX, L, PCT)
* `peso_liquido`, `peso_bruto` e `dimensoes` (largura, altura, profundidade — essenciais para cálculo de frete e ocupação de paletes)

* **Financeiro e Fiscal:**
* `preco_custo` (Preço da última compra ou custo médio ponderado)
* `preco_venda` e `margem_lucro`
* `ncm` (Nomenclatura Comum do Mercosul — obrigatório para emissão de Notas Fiscais no Brasil)
* `cest` (Código Especificador da Substituição Tributária)

* **Controle:**
* `status` (Ativo, Inativo, Descontinuado)

---

## 2. Estoque (A Relação Produto x Local)

> **Regra de Ouro de Arquitetura:** Nunca guarde a quantidade de estoque diretamente na tabela de Produto se o seu sistema puder evoluir para múltiplos locais (lojas, depósitos, filiais). Crie uma tabela intermediária.

* **Dados da Entidade:**
* `produto_id` (Chave estrangeira)
* `local_armazenamento_id` (Chave estrangeira para Depósito Central, Loja 1, Corredor A, etc.)
* `quantidade_atual` (Saldo real disponível)
* `quantidade_reservada` (Produtos vendidos, mas que ainda não saíram fisicamente do galpão)
* `estoque_minimo` (Gatilho para alerta de compras/ponto de pedido)
* `estoque_maximo` (Para evitar excesso de capital imobilizado)
* `lote` e `data_validade` (Cruciais para alimentos, medicamentos e cosméticos — controle PEPS/FIFO)

---

## 3. Fornecedor

Entidade que alimenta o sistema. Precisa conter dados fiscais completos para a validação de entrada de mercadorias.

* **Dados Cadastrais e Fiscais:**
* `id`
* `razao_social` e `nome_fantasia`
* `cnpj` e `inscricao_estadual` (ou `inscricao_municipal`)
* `regime_tributario` (Simples Nacional, Lucro Presumido, Lucro Real)

* **Contato e Logística:**
* `endereco_completo` (Rua, número, complemento, bairro, cidade, UF, CEP)
* `telefone`, `email` (Geral e Comercial)
* `nome_contato_vendedor`

* **Financeiro:**
* `prazo_entrega_medio` (Lead time em dias)
* `condicoes_pagamento_padrao` (Ex: 30/60 dias, boleto, Pix)
* `status` (Ativo, Bloqueado)

---

## 4. Entrada (Compra / Recebimento de Mercadoria)

Representa o momento em que o estoque é abastecido. Em sistemas modernos, a entrada é gerada quase 100% via importação do XML da NF-e (Nota Fiscal Eletrônica).

* **Cabeçalho da Entrada (`Entrada`):**
* `id`
* `fornecedor_id` (Chave estrangeira)
* `numero_nota_fiscal` e `serie_nf`
* `chave_acesso_nfe` (Os 44 dígitos da nota fiscal)
* `data_emissao_nf` e `data_recebimento` (Quando a mercadoria chegou fisicamente)
* `valor_produtos`, `valor_frete`, `valor_impostos` (ICMS, IPI, ST) e `valor_total_nota`
* `status_recebimento` (Pendente, Conferido, Divergente, Cancelado)

* **Itens da Entrada (`ItemEntrada` - Tabela Pivot):**
* `entrada_id` (Chave estrangeira)
* `produto_id` (Chave estrangeira)
* `quantidade_recebida`
* `preco_custo_unitario` (Nesta compra específica)
* `lote` e `validade` (Informados no recebimento)
* `cfop` (Código Fiscal de Operações e Prestações)

---

## 5. Saída (Venda / Consumo / Perda)

O registro de como e por que o produto deixou o estoque. Pode ser uma venda ao cliente final, uma transferência entre filiais, ou uma baixa por avaria/perda.

* **Cabeçalho da Saída (`Saida`):**
* `id`
* `cliente_id` (Opcional, se for venda interna ou perda)
* `tipo_saida` (Venda, Transferência, Descarte/Avaria, Uso e Consumo)
* `data_saida`
* `numero_documento_fiscal` (Se aplicável - NF-e / NFC-e)
* `valor_total`
* `usuario_id` (Quem realizou a operação)

* **Itens da Saída (`ItemSaida` - Tabela Pivot):**
* `saida_id` (Chave estrangeira)
* `produto_id` (Chave estrangeira)
* `quantidade_saida`
* `preco_venda_unitario` (Praticado no momento da saída)

---

## 6. Movimentação de Estoque (A Tabela de Auditoria)

> **Padrão de Projeto Essencial:** Nunca altere a tabela de estoque sem deixar uma trilha de migalhas de pão. Toda alteração de saldo deve gerar um registro de log imutável nesta tabela. Se o estoque mudou, o motivo está aqui.

* **Dados da Entidade:**
* `id`
* `produto_id` (Chave estrangeira)
* `local_armazenamento_id` (Chave estrangeira)
* `tipo_movimentacao` (Entrada por Compra, Saída por Venda, Ajuste Inventário (+), Ajuste Inventário (-), Transferência)
* `origem_id` (ID da tabela de `Entrada` ou `Saida` que gerou isso, para rastreabilidade)
* `quantidade` (Valor absoluto ou positivo/negativo)
* `saldo_anterior` e `saldo_posterior` (Para auditoria rápida de bugs de concorrência de banco)
* `data_movimentacao` (Timestamp gerado pelo banco)
* `usuario_id`
