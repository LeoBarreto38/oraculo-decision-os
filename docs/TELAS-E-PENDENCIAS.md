# Telas e pendências da v0

Este documento descreve a intenção funcional das telas e deixa explícito o que a v0 não pretende resolver.

## Navegação e telas

### Hoje

É a rota inicial. Mostra uma única meta principal, exatamente três prioridades, tarefas atrasadas, decisões pendentes, alertas, projetos sem avanço e próximo marco. O check-in livre registra feito, não feito, impedimentos, aprendizados e fatos que podem alterar a estratégia.

Limite: prioridade não é agenda automática. O usuário confirma o trabalho e informa o resultado.

### Painel

Resume caixa, renda, meta, gap, capital experimental, pipeline, projetos, decisões, hipóteses, alertas e gasto de IA. Os gráficos mostram progresso financeiro e distribuição de tempo entre `CASH`, `ASSET`, `LEARNING`, `MAINTENANCE` e `DISTRACTION`.

Limite: valores financeiros são registros manuais; não há integração bancária. Gráficos com pouco histórico são apenas descritivos.

### Decisões

Cria pergunta, opções, evidências e estimativas. O score é determinístico; a análise LLM, o red team e a recomendação ficam separados da decisão humana. Resultado e previsão fecham o ciclo para calibração.

Limite: scores de 0 a 10 e probabilidades continuam sujeitos a julgamento. Não existe otimização científica automática dos pesos.

### Projetos

Exibe `ACTIVE`, `VALIDATING`, `PAUSED`, `INVALIDATED`, `COMPLETED` e `ARCHIVED`, além de valor estratégico, receita potencial, tempo até valor, caixa, risco, validação e próxima ação.

Limite: o sistema alerta sobre fuga para projeto novo, mas não impede o usuário de decidir conscientemente.

### Metas

Mantém alvo, valor atual, unidade, prazo, prioridade e estado. A meta financeira do Estado Zero serve como âncora inicial.

Limite: o progresso depende de atualização manual ou de entidades já registradas; não há sincronização financeira.

### Hipóteses

Registra prior, probabilidade atual, definição de teste, condição de sucesso/falha e resolução. Hipóteses vencidas geram alerta.

Limite: a v0 não implementa atualização bayesiana geral. Mudanças de probabilidade precisam de evidência e registro.

### Mapa

Visualiza relações existentes entre pessoa, meta, projeto, decisão, hipótese, oportunidade, empresa, tecnologia, habilidade e evidência.

Limite: é um grafo de navegação/auditoria, não uma ontologia, banco vetorial ou motor semântico.

### Diário

Lista entradas com data, texto e tags; inclui o histórico de check-ins para revisão.

Limite: não há análise psicológica, criptografia por campo ou editor rico avançado.

### Oráculo

Conversa sobre os dados locais e pode preparar uma decisão, tarefa, hipótese ou evidência. Uma mutação relevante deve ser confirmada. A resposta deve separar evidência, inferência, risco, confiança e próxima ação.

Limite: a v0 não age fora do aplicativo, não mantém autonomia em segundo plano e não substitui avaliação humana.

### Configurações

Mostra parâmetros não secretos: modelos, orçamento, horários, pesquisa, retenção e regras. A chave não deve ser retornada pela API nem exibida.

Limite: alterações de ambiente exigem reinício da API. Pesos estratégicos não devem mudar sem uma Decision registrada.

## Pendências deliberadas

Ficam fora da v0:

- voz/realtime;
- aplicativo Android nativo;
- múltiplos usuários e autenticação;
- sincronização cloud;
- serviço residente do Windows;
- criptografia de banco/backup;
- banco vetorial, Postgres, Supabase, Redis e microserviços;
- modelos locais ou outros fornecedores;
- integrações bancárias;
- envio autônomo de mensagens, compras, contratos ou contratação;
- scraping contínuo;
- Monte Carlo avançado, regressões, modelos temporais e ML próprio.

## Limitações operacionais reais

- O scheduler e notificações dependem de a API estar em execução.
- A Notification API depende de permissão e comportamento do navegador.
- SQLite é single-user e não deve ter vários processos escritores.
- A PWA não transforma o backend em serviço offline; API local ainda precisa estar aberta.
- Pesquisa web e GPT exigem rede, chave válida, quota, cobrança e acesso ao modelo/ferramenta.
- O custo exibido é estimativa; confirme cobrança no painel OpenAI.
- O conhecimento do modelo tem limite temporal; use pesquisa quando atualidade importa.
- Calibração exige previsões resolvidas. No começo, “dados insuficientes” é o resultado correto.
- Backups locais protegem contra erro lógico/corrupção, mas não contra perda do próprio disco se nenhuma cópia segura existir.
- Dados e backups não são criptografados pela aplicação.

## Critério para qualquer expansão

Uma nova função só deve entrar se uma decisão registrada demonstrar que ela é necessária para o objetivo atual, supera seu custo de oportunidade e não serve como fuga da validação comercial. Primeiro conclua `DECISION-O-006` e use a v0 em decisões reais.
