# Teste de aceite da v0

Execute com um banco temporário ou depois de um backup. Não exponha segredos em capturas ou relatórios.

## 1. Instalação e isolamento

- [ ] A instalação termina sem erro em uma pasta escolhida pelo usuário.
- [ ] `GET /api/health` responde com sucesso em `127.0.0.1`.
- [ ] Um banco vazio recebe somente registros identificados como `DEMO`.
- [ ] Executar `init-db` novamente não duplica o seed.
- [ ] Um banco que já contém qualquer estado não recebe registros DEMO nem perde registros.
- [ ] `ORACULO_DATA_DIR`, `ORACULO_DATABASE_URL`, `ORACULO_ENV_FILE` e `ORACULO_TIMEZONE` funcionam sem alterar o código.

## 2. Dados DEMO

- [ ] Existe `DEMO: Demo User` no mapa.
- [ ] Existe uma meta mensurável, um projeto de exemplo e uma decisão com duas estratégias.
- [ ] Valores financeiros DEMO são neutros e não simulam dados reais de uma pessoa.
- [ ] O fallback do frontend mostra apenas o mesmo contexto neutro.

## 3. CRUD e decisão

- [ ] Criar e editar projeto, tarefa, meta e hipótese.
- [ ] Registrar check-in e diário; reiniciar e confirmar persistência.
- [ ] Criar decisão com duas opções, critérios, evidência e previsão.
- [ ] Executar análise determinística sem IA.
- [ ] Registrar decisão humana sem sobrescrever a recomendação.
- [ ] Registrar resultado e resolver previsão.

## 4. Recursos opcionais e segurança

- [ ] Desabilitar pesquisa web produz falha controlada quando ela é solicitada.
- [ ] Limites de custo bloqueiam novas chamadas conforme configurado.
- [ ] Chave não aparece no frontend, API, logs, build ou backup.
- [ ] Contexto enviado para IA lista somente registros necessários e IDs auditáveis.
- [ ] Nenhum endpoint executa compra, mensagem ou ação externa autônoma.

## 5. Backup e qualidade

- [ ] `python -m app.cli backup` cria um pacote no diretório configurado.
- [ ] O pacote não contém `.env.local` nem `OPENAI_API_KEY`.
- [ ] Um backup restaurado com processos encerrados preserva registros.
- [ ] `python -m pytest -q` passa.
- [ ] `pnpm run typecheck` passa.
- [ ] `pnpm run build` passa.
- [ ] Erros de rede ou provedor de IA não derrubam o CRUD local.

Registre data, versão, sistema operacional, itens reprovados e evidências. Falhas em segredo, persistência, isolamento de dados, decisão humana, limite rígido ou backup bloqueiam o aceite.
