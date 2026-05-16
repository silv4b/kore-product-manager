# Manual Docker: Gerenciamento de Imagens e Containers

## 1. Informações do Sistema

```bash
# Versão do Docker
docker version

# Informações detalhadas do Docker Engine
docker info
```

---

## 2. Gerenciamento de Imagens

### 2.1 Listar Imagens

```bash
# Listar todas as imagens
docker images

# Listar apenas IDs das imagens
docker images -q

# Listar imagens com filtro (ex: dangling)
docker images --filter dangling=true
```

### 2.2 Baixar Imagens

```bash
# Baixar uma imagem do Docker Hub
docker pull <imagem>:<tag>

# Exemplos
docker pull python:3.12-slim
docker pull postgres:16
docker pull nginx:alpine
```

### 2.3 Construir Imagens

```bash
# Construir uma imagem a partir de um Dockerfile
docker build -t <nome>:<tag> .

# Construir sem usar cache
docker build --no-cache -t <nome>:<tag> .

# Construir especificando um Dockerfile diferente
docker build -f Dockerfile.dev -t <nome>:<tag> .
```

### 2.4 Remover Imagens

```bash
# Remover uma imagem específica
docker rmi <imagem>

# Remover múltiplas imagens
docker rmi <imagem1> <imagem2>

# Remover todas as imagens não utilizadas (dangling)
docker image prune

# Remover todas as imagens não utilizadas (forçar)
docker image prune -a

# Remover todas as imagens do sistema
docker rmi $(docker images -q) -f
```

### 2.5 Taggear e Compartilhar

```bash
# Adicionar tag a uma imagem
docker tag <imagem>:<tag> <novo-nome>:<nova-tag>

# Enviar imagem para um registry
docker push <usuario>/<imagem>:<tag>
```

### 2.6 Inspecionar Imagens

```bash
# Inspecionar detalhes de uma imagem
docker inspect <imagem>

# Ver histórico de camadas
docker history <imagem>
```

---

## 3. Gerenciamento de Containers

### 3.1 Criar e Executar Containers

```bash
# Criar e iniciar um container
docker run <imagem>

# Executar em modo interativo com terminal
docker run -it <imagem> bash

# Executar em background (detached)
docker run -d <imagem>

# Mapear portas (host:container)
docker run -p 8080:80 <imagem>

# Definir nome para o container
docker run --name meu-container <imagem>

# Montar volume (bind mount)
docker run -v /host/path:/container/path <imagem>

# Definir variáveis de ambiente
docker run -e VARIAVEL=valor <imagem>

# Combinar opções comuns
docker run -d --name api -p 8000:8000 -e DEBUG=true minha-api:latest

# Remover automaticamente ao parar
docker run --rm <imagem>

# Executar com restart policy
docker run --restart always <imagem>
```

### 3.2 Listar Containers

```bash
# Listar containers em execução
docker ps

# Listar todos os containers (incluindo parados)
docker ps -a

# Listar apenas IDs dos containers em execução
docker ps -q

# Listar com filtro
docker ps --filter status=exited
docker ps --filter name=meu-container
```

### 3.3 Parar e Iniciar Containers

```bash
# Parar um container (envia SIGTERM)
docker stop <container>

# Parar todos os containers em execução
docker stop $(docker ps -q)

# Iniciar um container parado
docker start <container>

# Reiniciar um container
docker restart <container>

# Forçar parada (SIGKILL)
docker kill <container>

# Pausar/despausar processos
docker pause <container>
docker unpause <container>
```

### 3.4 Remover Containers

```bash
# Remover um container (deve estar parado)
docker rm <container>

# Remover container em execução (forçar)
docker rm -f <container>

# Remover todos os containers parados
docker container prune

# Remover todos os containers do sistema
docker rm $(docker ps -aq)
```

### 3.5 Logs e Monitoramento

```bash
# Ver logs de um container
docker logs <container>

# Seguir logs em tempo real
docker logs -f <container>

# Últimas N linhas
docker logs --tail 100 <container>

# Ver processos rodando no container
docker top <container>

# Ver uso de recursos (CPU, memória, rede)
docker stats

# Ver evento em tempo real do Docker daemon
docker events
```

### 3.6 Executar Comandos em Containers em Execução

```bash
# Executar comando interativo com terminal
docker exec -it <container> bash

# Executar comando sem terminal
docker exec <container> ls -la

# Executar como outro usuário
docker exec -u root <container> comando
```

### 3.7 Copiar Arquivos

```bash
# Copiar do host para o container
docker cp /host/arquivo.txt <container>:/caminho/

# Copiar do container para o host
docker cp <container>:/caminho/arquivo.txt ./host/

# Copiar de um container para outro
docker cp <container1>:/origem <container2>:/destino
```

---

## 4. Redes

```bash
# Listar redes
docker network ls

# Criar uma rede
docker network create minha-rede

# Conectar container a uma rede
docker network connect minha-rede <container>

# Desconectar container de uma rede
docker network disconnect minha-rede <container>

# Remover redes não utilizadas
docker network prune

# Inspecionar uma rede
docker network inspect minha-rede
```

---

## 5. Volumes

```bash
# Listar volumes
docker volume ls

# Criar um volume
docker volume create meu-volume

# Inspecionar um volume
docker volume inspect meu-volume

# Remover um volume
docker volume rm meu-volume

# Remover volumes não utilizados
docker volume prune
```

---

## 6. Limpeza Geral

```bash
# Remover containers parados, imagens não usadas, networks não usadas
docker system prune

# Remover tudo incluindo volumes (cuidado!)
docker system prune -a --volumes

# Ver uso de disco do Docker
docker system df
```

---

## 7. Docker Compose

```bash
# Iniciar serviços em background
docker compose up -d

# Iniciar e reconstruir imagens
docker compose up -d --build

# Parar serviços sem remover containers
docker compose stop

# Iniciar serviços parados
docker compose start

# Parar e remover containers, redes, volumes
docker compose down

# Parar e remover volumes também (cuidado: perde dados)
docker compose down -v

# Ver logs de todos os serviços
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f <servico>

# Executar comando em um serviço
docker compose exec <servico> bash

# Listar serviços
docker compose ps

# Reconstruir imagens sem cache
docker compose build --no-cache

# Puxar imagens atualizadas
docker compose pull
```

---

## 8. Dicas Rápidas

| Ação | Comando |
|------|---------|
| Acessar container | `docker exec -it <container> bash` |
| Parar todos containers | `docker stop $(docker ps -q)` |
| Remover todos containers | `docker rm $(docker ps -aq)` |
| Remover todas imagens | `docker rmi $(docker images -q) -f` |
| Limpeza completa | `docker system prune -a` |
| Ver logs em tempo real | `docker logs -f <container>` |
| Mapear porta | `docker run -p 8080:80 <imagem>` |
| Nomear container | `docker run --name meu-container <imagem>` |
