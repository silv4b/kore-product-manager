# Roadmap de Funcionalidades - Kore Manager

Este documento detalha as futuras melhorias e funcionalidades planejadas para o projeto, com passos técnicos para implementação.

## 1. Organização e Enriquecimento de Dados

### Sistema de Categorias

Permitir a classificação de produtos para melhor organização.

- [x] **Model**: Criar `Category(name, slug, description, color)`.
- [x] **Relacionamento**: Alterar para `ManyToManyField` (Múltiplas categorias por produto).
- [x] **Gerenciamento**: Criar sessão de gerenciamento (CRUD) de categorias.
- [x] **Funcionalidade**: Duplicação de categorias existentes.
- [x] **Automação**: Geração de Slug em tempo real com tratamento de acentos.
- [x] **UX**: Busca avançada de categorias (Nome, Descrição e Slug).
- [x] **UI**: Filtro de categorias pesquisável (Command-style) no catálogo.
- [x] **Consistência**: Padronização de botões (ghost/boxy) e badges de status/etiquetas.
- [x] **Estado Vazio**: Mensagens contextuais para buscas sem resultado em categorias.

### Suporte a Imagens de Produtos

Tornar o catálogo visualmente atraente.

- [ ] **Dependência**: Instalar `Pillow`.
- [ ] **Model**: Adicionar `ImageField` ao `Product` com uma imagem padrão (placeholder).
- [ ] **Forms**: Atualizar `ProductForm` para suportar upload de arquivos (`enctype="multipart/form-data"`).
- [ ] **Frontend**: Atualizar o "Grid View" para exibir a imagem como destaque do card.

### Histórico de Preços

Rastrear a flutuação de valor dos itens.

- [ ] **Model**: Criar `PriceHistory(product, price, date)`.
- [ ] **Signals**: Usar um `post_save` no `Product` para registrar mudanças de preço.
- [ ] **Visualização**: Adicionar um mini-gráfico (Sparkline) no modal de detalhes do produto.

## 2. Melhorias de UX com HTMX (Foco em Performance)

### Busca em Tempo Real (Live Search)

Filtragem instantânea sem recarregamento de página.

- [ ] **Template**: Adicionar atributos HTMX ao campo de busca:
  - `hx-get="{% url 'product_list' %}"`
  - `hx-trigger="keyup changed delay:500ms, search"`
  - `hx-target="#product-list-container"`
- [ ] **Backend**: Criar um template parcial (`_product_list_items.html`) que retorna apenas a lista de produtos.

### Edição de Estoque In-line

Alterar quantidades diretamente na tabela ou grid.

- [ ] **UI**: Adicionar botões de `+` e `-` ao lado da quantidade de estoque.
- [ ] **HTMX**: Usar `hx-post` para enviar a atualização silenciosamente.
- [ ] **Feedback**: Atualizar apenas o contador de estoque e o valor total do inventário no topo (OOB Swaps).

## 3. Automação e Inteligência

### Alertas de Estoque Baixo

Identificar proativamente produtos que precisam de reposição.

- [ ] **Model**: Adicionar `low_stock_threshold` (mínimo desejado) ao `Product`.
- [ ] **UI**: Criar um badge de alerta (ex: "Reposição Necessária") quando `stock <= low_stock_threshold`.
- [ ] **Dashboard**: Adicionar um card de resumo com o número total de itens abaixo do limite.

### Dashboard com Gráficos

Visualização executiva dos dados.

- [ ] **Lib**: Integrar `Chart.js` ou `ApexCharts`.
- [ ] **Dados**: Criar um endpoint JSON que retorna:
  - Distribuição de valor por categoria.
  - Evolução do valor total do estoque nos últimos 30 dias.

## 4. Gestão Avançada de Dados

### Importação e Exportação (CSV/Excel)

Facilitar o manejo de grandes volumes de dados.

- [ ] **Export**: Criar view que gera um `HttpResponse` com `content_type='text/csv'`.
- [ ] **Import**: Criar formulário de upload que lê CSV usando a biblioteca nativa `csv` do Python e cria objetos `Product` em massa.

### Ações em Massa (Bulk Actions)

- [ ] **UI**: Adicionar checkboxes em cada linha da tabela.
- [ ] **Funcionalidade**: Botões globais para "Excluir Selecionados" ou "Tornar Públicos" em um único clique.

## Próximos Passos Sugeridos

1. **Prioridade 1**: Suporte a Imagens de Produtos (Crucial para visual do catálogo).
2. **Prioridade 2**: Busca em tempo real com HTMX (Interatividade e velocidade).
3. **Prioridade 3**: Alertas de Estoque Baixo (Utilidade prática de gestão).
