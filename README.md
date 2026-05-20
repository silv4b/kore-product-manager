# Kore Product Manager

O Kore é um sistema de gerenciamento de inventário de produtos moderno, construído com foco em experiência do usuário, criado para testar o uso do Basecoat UI em um projeto Django.

## Tecnologias

O projeto utiliza as seguintes tecnologias:

- Backend: [Python](https://www.python.org/) 3.14+ [Django](https://www.djangoproject.com/) 6.0+
- Frontend: HTML5, JavaScript (Vanilla)
- API: [Django Rest Framework](https://www.django-rest-framework.org/), [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/), [drf-spectacular](https://drf-spectacular.readthedocs.io/)
- Estilização: [Tailwind CSS](https://tailwindcss.com/) v4.0+
- UI Framework: [Basecoat UI](https://basecoatui.com/)
- Autenticação: [Django Allauth](https://docs.allauth.org/en/latest/) e JWT para API
- Banco de Dados: [SQLite3](https://sqlite.org/) ou [PostgreSQL](https://www.postgresql.org/)
- Ícones: [Lucide Icons](https://lucide.dev/) (via CDN)

## Funcionalidades Principais

- **Gestão de Produtos**: CRUD completo (Criação, Visualização, Edição e Exclusão) de produtos.
- **Gestão de Fornecedores**: CRUD completo e vinculação a produtos de forma opcional.
- **Controle de Custo e Margens**: Registro de preço de custo, cálculo automático da margem de lucro e destaque visual de estoque crítico.
- **Dashboard de Estoque**: Histórico de movimentações (Entradas/Saídas) com estatísticas detalhadas.
- **Painel de Giro e Lucratividade (Relatórios)**: Indicadores de giro, valor total em estoque, estimativa de faturamento e ticket médio.
- **Navegação Moderna (Sidebar)**: Layout com barra lateral responsiva, grupos de acesso e recolhimento no desktop/mobile.
- **Histórico de Preços**: Rastreamento automático de mudanças de preço com visualização em gráfico (sparkline).
- **API REST**: Endpoints para integração com outras aplicações, incluindo documentação Swagger e ReDoc.
- **Visibilidade de Produtos**: Suporte para produtos públicos (catálogo global) e privados (visíveis apenas pelo dono).
- **Sistema de Notificações**: Toasts globais para feedback em tempo real das ações do usuário.
- **Interface Adaptativa**: Modo Escuro (Dark Mode) e Modo Claro inteligente com alternância fluida.

## Como Executar o Projeto

### Pré-requisitos

- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes e ambientes Python).
  - `pip install uv` ou [chaque a documentação](https://docs.astral.sh/uv/getting-started/installation/).
- Node.js (para compilação do CSS).

### Passos para Instalação

1. Clone o repositório para sua máquina local.

2. Instale as dependências do Python:
   `uv sync`

3. Instale as dependências do Node.js:
   `npm install`

4. Configure as variáveis de ambiente (Opcional):
   Crie um arquivo `.env` baseado no `.env.example`. Se não configurado, o sistema usará SQLite por padrão.

5. Execute as migrações do banco de dados:
   `uv run manage.py migrate`

### Executando a Aplicação

Para rodar o projeto, você precisará compilar o CSS e iniciar o servidor de desenvolvimento:

1. Compilação do Tailwind CSS:
   `npm run build` (ou `npm run watch` para observar alterações)

2. Servidor de Desenvolvimento:
   `uv run manage.py runserver`

A aplicação estará disponível em: <http://127.0.0.1:8000/>

### Atalhos PoeThePoet

O projeto utiliza o **PoeThePoet** para simplificar comandos frequentes. Você pode rodar:

- `uv run poe runserver`: Executa o servidor Django
- `uv run poe npm-build`: Compila o CSS do Tailwind + Basecoat
- `uv run poe pytest`: Roda a suíte completa de testes automatizados com SQLite
- `uv run poe coverage`: Executa testes e exibe cobertura de código

### Acessando a API

A API REST está disponível no prefixo `/api/v1/`.
Para documentação interativa, acesse:

- **Swagger UI**: <http://127.0.0.1:8000/api/v1/docs/swagger/>
- **ReDoc**: <http://127.0.0.1:8000/api/v1/docs/redoc/>

## Documentação Adicional

Para mais guias e configurações, consulte a pasta `docs/`:

- [Guia de Configuração do Ambiente de Desenvolvimento](docs/setup-ambiente-desenvolvimento.md)
- [Uso de UV e PoeThePoet](docs/uv-and-poethepoet.md)
- [Configuração Docker e PostgreSQL](docs/setup-docker-postgres.md)
- [Manual de Implantação e Docker](docs/manual-docker.md)
- [Validação de E-mail com Django-Allauth](docs/django-allauth-email-validation.md)
- [Login Social (Google e GitHub) com Django-Allauth](docs/django-allauth-social-login.md)
- [Guia Detalhado do Django-Allauth](docs/django-allauth-tutorial.md)
- [Adicionando Basecoat UI ao Django](docs/adicionando-basecoat-ui.md)
- [Plano de Ação da Refatoração](docs/plano-de-acao.md)
- [Roadmap do Projeto](docs/kore-product-roadmap.md)
