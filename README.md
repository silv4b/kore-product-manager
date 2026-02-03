# Product Django Manager

O Kore é um sistema de gerenciamento de inventário de produtos moderno, construído com foco em experiência do usuário, criado para testar o uso do Basecoat UI em um projeto Django.

## Tecnologias

O projeto utiliza as seguintes tecnologias:

- Backend: Django (Python) 6.0+
- Frontend: HTML5, JavaScript (Vanilla)
- Estilização: Tailwind CSS v4.0+
- UI Framework: Basecoat UI
- Autenticação: Django Allauth
- Banco de Dados: SQLite3
- Ícones: Lucide Icons (via CDN)

## Funcionalidades Principais

- Gestão de Produtos: CRUD completo (Criação, Visualização, Edição e Exclusão) de produtos.
- Painel de Controle: Dashboard com estatísticas e alternância entre modos de visualização (Grade e Tabela).
- Visibilidade de Produtos: Suporte para produtos públicos (catálogo global) e privados (visíveis apenas pelo dono).
- Sistema de Notificações: Toasts globais para feedback em tempo real das ações do usuário.
- Segurança do Usuário:
  - Validação de força de senha em tempo real no cadastro e alteração.
  - Alternância de visibilidade de senha (mostrar/esconder).
  - Gerenciamento de perfil e exclusão permanente de conta.
- Interface Adaptativa: Modo Escuro (Dark Mode) e Modo Claro inteligente com alternância fluida.

## Como Executar o Projeto

### Pré-requisitos

- Python 3.10 ou superior.
- Node.js (para compilação do CSS).
- Pip (gerenciador de pacotes do Python).

### Passos para Instalação

1. Clone o repositório para sua máquina local.

2. Crie e ative um ambiente virtual:
   - `python -m venv venv`
   - `.\venv\Scripts\activate`  (Windows)
   - `source venv/bin/activate` (Linux/macOS)

3. Instale as dependências do Django:
   `pip install django django-allauth` e requirements.txt

4. Instale as dependências do Node.js:
   `npm install`

5. Execute as migrações do banco de dados:
   `python manage.py makemigrations`
   - `python manage.py migrate`

### Executando a Aplicação

Para rodar o projeto, você precisará de dois processos rodando (ou buildar o CSS antes):

1. Compilação do Tailwind CSS (em um terminal):
   npm run watch

   (Ou para build de produção: npm run build)

2. Servidor de Desenvolvimento (em outro terminal):
   python manage.py runserver

A aplicação estará disponível em: <http://127.0.0.1:8000/>
