# Quick Start - Sistema Multi-Cursos D2L (LOGIN ÚNICO)

## 📋 Visão Geral

Sistema parametrizado para extrair conteúdo de múltiplos cursos D2L com **LOGIN ÚNICO COMPARTILHADO**.

🔑 **Vantagem**: Faz login apenas UMA VEZ e reutiliza a sessão para todos os cursos, economizando tempo e evitando múltiplas autenticações 2FA.

## 🚀 Uso Rápido

### Opção 1: Script Orquestrador com Login Único (Recomendado)

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Processar um único curso
python3 process_course.py --course-id 2001539

# Processar múltiplos cursos com LOGIN ÚNICO
python3 process_course.py --course-ids 2001540 2001539

# Processar 5 cursos com login único
python3 process_course.py --course-ids 2001540 2001539 2001541 2001542 2001543
```

### Opção 2: Scripts Individuais

```bash
# Passo 1: Extrair página home
python3 extract_content_home.py --course-id 2001539

# Passo 2: Crawl dos links
python3 extract_links_crawler.py --course-id 2001539
```

## 📁 Estrutura de Saída

```
data/
├── course_2001540/           # Curso MLO
│   ├── content_home_2001540.json
│   ├── Account_Settings.json
│   ├── Progress.json
│   ├── Content.json
│   ├── Final_Project_Report.json
│   ├── Final_Project_Code.json
│   └── _summary.json
│
└── course_2001539/           # Novo curso
    ├── content_home_2001539.json
    ├── (links extraídos...)
    └── _summary.json
```

## 🔧 Parâmetros Disponíveis

### extract_content_home.py

```bash
--course-id    # ID do curso (padrão: 2001540)
--output       # Arquivo de saída customizado
```

### extract_links_crawler.py

```bash
--course-id    # ID do curso (padrão: 2001540)
--input        # Arquivo JSON de entrada
--output-dir   # Diretório de saída customizado
```

### process_course.py

```bash
--course-id     # Processar um único curso
--course-ids    # Processar múltiplos cursos (separados por espaço)
--output-base   # Diretório base para saída
```

## 📊 Exemplos Práticos

### Exemplo 1: Adicionar Novo Curso

```bash
# Processar curso 2001539
python3 process_course.py --course-id 2001539

# Resultado:
# - data/course_2001539/content_home_2001539.json
# - data/course_2001539/*.json (todos os links)
# - data/course_2001539/_summary.json
```

### Exemplo 2: Processar Lote de Cursos

```bash
# Processar 3 cursos com LOGIN ÚNICO
python3 process_course.py --course-ids 2001540 2001539 2001541

# O sistema:
# 1. Faz login UMA ÚNICA VEZ (com 2FA se necessário)
# 2. Reutiliza a sessão autenticada para TODOS os cursos
# 3. Processa cada curso sequencialmente
# 4. Gera resumo final com estatísticas

# Vantagem: Você só precisa aprovar o 2FA UMA VEZ!
```

### Exemplo 3: Re-processar Curso Específico

```bash
# Apenas extrair home novamente
python3 extract_content_home.py --course-id 2001540

# Apenas crawl links novamente (usa JSON existente)
python3 extract_links_crawler.py --course-id 2001540
```

## ⚙️ Configuração

1. **Credenciais** - Configure no `.env`:
   ```env
   D2L_USERNAME='seu_email@fanshaweonline.ca'
   D2L_PASSWORD='sua_senha'
   ```

2. **Autenticação 2FA** - O script detecta e mostra o código automaticamente

## 📝 Notas

- **Login único**: O sistema faz login UMA ÚNICA VEZ e reutiliza a sessão autenticada para todos os cursos
- **2FA otimizado**: Você só precisa aprovar o 2FA UMA VEZ, não para cada curso
- **Organização**: Cada curso tem sua própria pasta em `data/course_{id}/`
- **Resumo**: Arquivo `_summary.json` contém estatísticas de cada curso
- **Retrocompatível**: Scripts individuais ainda funcionam independentemente

## 🔍 Verificar Resultados

```bash
# Ver estrutura de pastas
ls -la data/

# Ver resumo de um curso
cat data/course_2001539/_summary.json | jq

# Ver links extraídos
ls -lh data/course_2001539/*.json
```

## ❓ Troubleshooting

### Erro: "Arquivo content_home_X.json não encontrado"
```bash
# Execute primeiro a extração da home
python3 extract_content_home.py --course-id X
```

### Erro: "Configure D2L_USERNAME e D2L_PASSWORD"
```bash
# Verifique o arquivo .env
cat .env | grep D2L
```

### 2FA não funciona
```bash
# O código é mostrado no terminal
# Digite manualmente no app Microsoft Authenticator
```

## 📚 Próximos Passos

1. Adicionar mais cursos à lista
2. Automatizar via cron/scheduler
3. Integrar com pipeline de dados
4. Adicionar notificações de conclusão
