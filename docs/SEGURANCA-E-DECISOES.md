# Segurança, privacidade e decisão humana

## Fronteira de autonomia

O Oráculo pode ler dados registrados, calcular scores, solicitar análise, pesquisar fontes atuais quando autorizado e propor próximos passos. Ele não pode, na v0:

- gastar dinheiro;
- contratar serviço;
- enviar mensagem ou publicar conteúdo;
- aceitar contrato;
- alterar pesos de decisão silenciosamente;
- criar ou alterar registro relevante sem confirmação na experiência de chat;
- transformar recomendação em decisão humana automaticamente.

Uma decisão irreversível ou de alto custo exige mais evidência e confirmação explícita. A interface deve apresentar recomendação, justificativa, evidências, premissas, risco principal, condição de mudança, confiança, próxima ação e data de revisão.

## O que é fato e o que é inferência

Cada insumo deve manter sua proveniência:

- `USER_STATEMENT` e `PERSONAL_DATA`: fornecidos/registrados pelo usuário;
- `MARKET_DATA` e `WEB`: fonte externa atual, com data e URL;
- `EXPERIMENT` e `OBSERVATION`: resultado observado;
- `MODEL_INFERENCE`: síntese ou inferência do modelo, não evidência independente.

Texto eloquente não aumenta força da evidência. Pesquisa atual não deve ser misturada silenciosamente ao conhecimento do modelo.

## Contexto mínimo

O backend, e nunca o frontend, monta o contexto da chamada:

```text
CORE_CONTEXT
  + GOAL_CONTEXT
  + PROJECT_CONTEXT
  + DECISION_CONTEXT
  + RELEVANT_HISTORY
  + EVIDENCE
```

Não envie o banco completo. Inclua apenas dados necessários à pergunta atual e preserve uma trilha auditável dos registros selecionados. Antes de registrar informação altamente sensível, considere se ela é necessária para a decisão.

## Segredos

- segredo local: `.env.local` na raiz do projeto, ou arquivo indicado por `ORACULO_ENV_FILE`;
- variável: `OPENAI_API_KEY`;
- uso: somente processo backend;
- exemplo público: chave vazia;
- logs, banco, respostas HTTP, frontend, backup e Git: nunca devem conter a chave.

Se houver suspeita de exposição, revogue a chave no projeto OpenAI, crie outra dedicada e substitua somente no arquivo local. Não tente “limpar” o problema apenas apagando uma mensagem ou commit.

## Dados locais

SQLite e backups não são criptografados na v0. A proteção depende da conta Windows, BitLocker quando disponível, permissões do diretório e cuidado com exportações. Não coloque `data` em compartilhamento público ou sincronização automática sem revisar riscos.

O servidor está vinculado a `127.0.0.1`. A v0 não oferece login, controle de acesso ou isolamento entre usuários; por isso não deve ser exposta à LAN ou internet.

## Chamadas externas

Uma análise OpenAI envia o contexto selecionado para a API. Pesquisa web também envia a consulta e recebe fontes externas. Exiba essa distinção antes da ação sempre que houver material pessoal relevante.

Os modos locais — cadastro, cálculo determinístico, consulta ao banco, Brier Score, mapa e backup — devem continuar independentes de uma chamada de IA, salvo quando a própria função exigir análise.

## Orçamento e falhas

O limite interno é uma barreira operacional, não garantia de faturamento. Estimativas podem divergir por cache, ferramentas, preços e chamadas que ocorram fora do aplicativo. Configure também controles na conta OpenAI.

No limite rígido:

1. pare chamadas automáticas;
2. preserve a tarefa/decisão pendente;
3. mostre o motivo;
4. exija autorização explícita;
5. registre a continuação, se aprovada.

Não troque silenciosamente um modelo crítico por outro para contornar limite ou falta de acesso.

## Limites éticos

- O score determinístico é comparativo, não “verdade matemática”.
- Probabilidades são julgamentos calibráveis, não garantias.
- Poucas previsões devem resultar em “DADOS INSUFICIENTES PARA CALIBRAÇÃO”.
- O padrão de rejeição/perfeccionismo é hipótese histórica; não diagnostique saúde mental.
- Não use motivação automática para mascarar evidência ruim.
- Questões médicas, jurídicas, financeiras reguladas ou de risco pessoal exigem fontes e profissionais adequados.
- Sempre registre o que faria a recomendação mudar.

## Revisão de uma decisão crítica

Antes de confirmar:

- [ ] objetivo e restrições estão explícitos;
- [ ] opções reais incluem “não agir” quando pertinente;
- [ ] dados ausentes foram identificados;
- [ ] evidências têm origem e data;
- [ ] score e pesos estão visíveis;
- [ ] custo de oportunidade foi considerado;
- [ ] reversibilidade foi avaliada;
- [ ] red team procurou premissas frágeis e custos ocultos;
- [ ] confiança corresponde à força da evidência;
- [ ] próxima ação é pequena e verificável;
- [ ] revisão e resultado futuro podem ser registrados;
- [ ] decisão final foi tomada por uma pessoa.
