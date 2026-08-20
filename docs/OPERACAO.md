# Operação local

Este guia cobre inicialização, configuração, backup e diagnóstico em Windows, Linux e macOS.

## Contrato operacional

- aplicação e API: `http://127.0.0.1:8000`;
- saúde: `http://127.0.0.1:8000/api/health`;
- banco default: `data/oraculo.db`, relativo à raiz do projeto;
- ambiente default: `.env.local`, na raiz do projeto;
- um processo Python/Uvicorn serve API e `frontend/dist`;
- instalação local, single-user e sem Docker obrigatório.

## Configuração

Copie `.env.example` para `.env.local` e edite apenas a cópia local. Reinicie a API após mudanças.

- `ORACULO_ENV_FILE` seleciona outro arquivo de ambiente;
- `ORACULO_DATA_DIR` seleciona o diretório de dados;
- `ORACULO_DATABASE_URL` substitui a URL SQLite derivada do diretório de dados;
- `ORACULO_TIMEZONE` aceita um fuso IANA e usa `UTC` por padrão;
- `ORACULO_MODEL_*`, limites de custo, horários, CORS e logs permanecem configuráveis.

Caminhos relativos em `ORACULO_DATA_DIR` são resolvidos a partir da raiz do projeto. Use caminhos absolutos somente quando a instalação realmente exigir.

## Inicialização

No Windows, use `install-oraculo.bat` e `start-oraculo.bat`. Em qualquer plataforma, a forma manual é:

```bash
cd backend
python -m app.cli init-db
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

O seed só cria registros `DEMO` em banco vazio. Se qualquer estado de usuário existir, ele retorna sem escrever. Migrações de schema continuam idempotentes e não substituem registros.

## Encerramento

Pressione `Ctrl+C` no terminal do backend. Encerre também o Vite caso esteja executando `pnpm run dev`. Aguarde os processos terminarem antes de copiar ou restaurar o SQLite.

## Backup manual

```bash
cd backend
python -m app.cli backup
```

O pacote é criado em `data/backups` por padrão, ou sob o diretório definido em `ORACULO_DATA_DIR`. Ele pode conter diário, decisões, evidências e dados financeiros; não o publique.

### Restauração conservadora

1. Encerre todos os processos do Oráculo.
2. Copie o banco atual para um arquivo de segurança datado.
3. Confirme que o backup pertence à instalação correta.
4. Restaure o SQLite no caminho configurado.
5. Execute `python -m app.cli init-db` para aplicar apenas operações idempotentes.
6. Inicie e confirme `/api/health` e seus registros recentes.

Não restaure sobre um banco aberto e não trate exportação JSON como SQLite.

## Testes e diagnóstico

```bash
cd backend
python -m pytest -q

cd ../frontend
pnpm run typecheck
pnpm run build
```

Com o sistema iniciado, verifique `/api/health`. Se a API falhar, confira o ambiente virtual, permissão de escrita no diretório de dados, formato das variáveis, disponibilidade da porta 8000 e o erro completo do terminal. Nunca imprima o valor de uma chave para diagnosticar.

SQLite é apropriado para um usuário e um backend. Evite banco em pasta sincronizada e ferramentas que mantenham lock de escrita. Mantenha o servidor em `127.0.0.1`; expor em rede exige autenticação, TLS e regras de firewall.
