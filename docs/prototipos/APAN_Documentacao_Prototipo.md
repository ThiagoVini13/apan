# Protótipo do sistema APAN de frequência escolar

Este documento apresenta o protótipo visual do APAN, explica suas principais telas e reúne as decisões de acessibilidade, atratividade e os wireframes solicitados na atividade. A proposta é facilitar o registro de presença, o cadastro de alunos e o acompanhamento da frequência.

O projeto é uma plataforma de frequência escolar. Por isso, o rascunho solicitado é apresentado como wireframes de telas; a parte sobre tipos de jogos não se aplica a esta proposta.

## 1 Visão geral e tela inicial

**Figura 1:** Tela inicial do protótipo com resumo do dia e atalhos.

A tela inicial reúne turmas ativas, chamadas concluídas e presença do dia. Os atalhos Fazer chamada, Adicionar aluno e Extrair relatório levam às tarefas mais frequentes. Os cartões das turmas mostram horário, disciplina, sala e situação da chamada.

O menu mantém as opções Início, Chamada, Alunos e Relatórios. O perfil exibido no exemplo é o de professora. Os nomes, datas e indicadores das imagens são dados demonstrativos do protótipo.

## 2 Registro de frequência

**Figura 2:** Chamada com seleção de turma e marcação por aluno.

O professor seleciona a turma, a data da aula e a disciplina. Na lista, cada aluno tem nome, matrícula e as opções Presente e Ausente. Os contadores mostram quantos alunos estão presentes, ausentes ou sem marcação.

A opção Marcar todos como presentes agiliza a chamada: depois de usá-la, o professor ajusta as ausências. O campo de anotações permite registrar conteúdo trabalhado e ocorrências, com limite de 1000 caracteres.

Para concluir, o professor revisa as marcações e aciona Salvar frequência. No modo mostrado, o protótipo impede o salvamento quando há alunos sem marcação e direciona o foco ao primeiro registro pendente. Quando a chamada é salva, aparece uma mensagem de confirmação.

A lista ocupa uma área com rolagem; a ação de salvar permanece no rodapé. Essa organização mantém a tarefa principal visível durante a chamada.

## 3 Consulta e cadastro de alunos

**Figura 3:** Consulta com busca, filtros e frequência por aluno.

A tela Alunos permite pesquisar pelo nome e filtrar por turma e turno. A tabela reúne matrícula, turma, nascimento e frequência. A ação Editar abre os dados do aluno; Novo aluno inicia o cadastro.

**Figura 4:** Formulário de cadastro exibido sobre a lista.

O formulário solicita nome, nascimento, turma, responsável e telefone. Os erros são descritos junto aos campos e o foco é direcionado ao primeiro campo inválido. Cancelar fecha o formulário; Cadastrar aluno confirma a inclusão na demonstração.

## 4 Acompanhamento e relatórios

**Figura 5:** Relatório com filtros, gráficos e lista de acompanhamento.

O usuário informa o período e escolhe turma e aluno. Os atalhos Setembro, 3º bimestre e Ano letivo preenchem intervalos de consulta. A tela apresenta o total de presenças e faltas, a presença por turma e os alunos com mais faltas.

Os números aparecem junto aos gráficos, permitindo interpretar os resultados sem depender somente das cores. O protótipo destaca valores abaixo de 75%; esse é o parâmetro usado na demonstração e deverá ser confirmado conforme as regras da instituição.

### Limites da demonstração

Os percentuais e os dados dos relatórios são simulados. A opção de exportação permite escolher XLSX ou CSV e apresenta uma confirmação visual, mas o código não gera nem baixa uma planilha real. O botão Sair também simula uma mensagem, sem autenticação.

O cadastro e a chamada alteram o estado da página, sem gravação permanente em banco de dados. Para o sistema final, será necessário guardar a frequência por aluno, turma, data e disciplina, integrar os relatórios aos registros reais e definir as permissões de cada perfil.

## 5 Acessibilidade e atratividade

A interface usa fundo claro, áreas brancas e texto escuro. O azul identifica as ações principais; verde e vermelho indicam situações da frequência. As escolhas visuais buscam facilitar a leitura e a identificação das tarefas.

| Aspecto | Aplicação no protótipo |
| :--- | :--- |
| **Cores** | Azul #1A56DB para ações; fundo #F4F6F9; superfícies #FFFFFF; texto #14181F e #4B5563. |
| **Leitura** | Títulos organizam as seções; nomes, matrículas e rótulos descrevem as informações. |
| **Uso das cores** | Presente e Ausente aparecem escritos. Alertas combinam texto e símbolo; os gráficos apresentam valores. |
| **Teclado** | Há estilo de foco visível e botões nativos. A chamada orienta o uso de Tab, Espaço e Enter. |
| **Formulários** | Os campos possuem rótulos e indicação de erro com aria-invalid e aria-describedby. |
| **Mensagens** | As confirmações usam uma região de status com aria-live para anunciar alterações. |
| **Tamanho e adaptação** | Diversos controles têm altura mínima de 44 px. Em telas estreitas, a navegação passa para a parte inferior. |
| **Simplicidade** | Atalhos, filtros, contadores e marcação coletiva reduzem etapas da tarefa. |

### Verificações e ajustes para a versão final

A presença desses recursos no código não comprova acessibilidade completa. É necessário testar a navegação inteira por teclado, a leitura com leitor de tela, a ampliação de texto e o uso em celular.

O link Pular para o conteúdo usa uma indicação de estilo de foco que deve ser verificada no navegador. No formulário, devem ser testados a contenção do foco dentro do diálogo e o retorno ao botão de origem após fechá-lo.

Também é preciso medir o contraste de textos, bordas e estados dos controles. As bordas claras de campos e botões merecem revisão. A atratividade vem da organização, dos espaços e do retorno das ações; a prioridade do sistema é executar a chamada com poucos passos.

## 6 Wireframes e fluxo de uso

Os wireframes abaixo foram elaborados a partir das telas do protótipo. Eles simplificam a interface em blocos para mostrar a posição das informações e das ações, sem depender das cores e dos detalhes visuais.

**Figura 6:** Wireframes das quatro áreas principais do APAN.

### Fluxo da chamada

1. Entrar na tela inicial e identificar a turma com chamada pendente.
2. Abrir Fazer chamada e conferir turma, data e disciplina.
3. Marcar Presente ou Ausente para cada aluno.
4. Conferir os contadores e registrar anotações, se necessário.
5. Salvar frequência e verificar a confirmação.

### Relação com os pontos da atividade

O primeiro ponto é atendido pelas capturas das telas e pelas explicações de uso. O segundo é tratado pelas decisões visuais, pelos recursos de acessibilidade e pelos ajustes indicados. O terceiro é atendido pelos wireframes e pelo fluxo da chamada.

Base do documento: arquivo APAN Frequência Escolar.html fornecido para a atividade. As capturas mostram a interface original; os wireframes são esquemas elaborados para esta documentação.
