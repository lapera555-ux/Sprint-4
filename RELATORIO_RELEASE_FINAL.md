# SOMPO Agro | Relatório de revisão da interface e integridade do release

## Escopo entregue

A edição leve foi derivada da instalação científica real anterior. A edição completa acrescenta os arquivos originais fornecidos pelo usuário. O projeto preserva o código Python, SQLite preenchido, modelos treinados, migrações 001–009, views e logs. Uma correção independente atualiza apenas a interface e inclui opção de anexar os dois arquivos originais a uma instalação existente.

## Ajustes executados

- Interface `src/agro_ui.py`: fontes exibidas em blocos explicativos; tabela compacta com nomes curtos; nomes científicos integrais e SHA mantidos no detalhe, no SQLite e no CSV.
- Gráficos agrícolas passam a usar uma especificação Vega-Lite explícita (`src/ui_layout.py`). O eixo horizontal cobre a primeira até a última linha representada na fonte (não começa em valores negativos); o índice é sempre apresentado como 0 a 100.
- Tabela de janelas e investigações mostra primeiro as colunas relevantes e disponibiliza os dados técnicos completos em um expansor. Glossário não depende de tabela larga.
- A interface distingue os arquivos brutos presentes da versão leve sem brutos; não declara falsamente que os `.tab` acompanham qualquer edição.
- Instalador `scripts/attach_original_sources.py` valida SHA-256 do ZIP Tümosan, do ZIP UCI e dos dez membros `.tab`, recusa divergência e não substitui banco ou modelos.
- Script separado atualiza a interface do Windows em uma pasta anterior com backup de código e comparação de hashes do SQLite e `.joblib` antes/depois.

## Resultado de testes executados neste ambiente

| Verificação | Resultado |
|---|---|
| Suíte de testes completa | 53 aprovados; 1 ignorado por falta de Streamlit neste ambiente |
| Integridade SQLite | `ok` |
| Chaves estrangeiras | 0 erros |
| Arquivos de origem Tümosan | ZIP e 10 `.tab` conferidos com os hashes locais declarados |
| UCI hidráulica | ZIP conferido com hash local declarado |
| Verificador estrito, edição completa | `PASS_WITH_DECLARED_SOURCE`, 0 questões pendentes internas |
| Trator | 10 arquivos, 889.255 linhas, 895 janelas e 895 escores |
| Investigações agrícolas | 40 registros |
| Hidráulica | 2.205 ciclos; 450 previsões no teste retido |
| Teste do reparo sobre instalação anterior isolada | Preservou SHA-256 dos dados/modelos, 53 testes aprovados |

A ressalva `PASS_WITH_DECLARED_SOURCE` significa que a origem foi declarada pelo usuário, e os hashes locais foram comparados. Não representa autenticação independente do checksum do editor científico. Os 889.255 dados brutos não são 889.255 linhas SQL, porque o SQLite persiste janelas resumidas; a edição completa guarda os `.tab` para reconstrução.

## Aceite restante fora deste ambiente

A interface já foi aberta em Windows pelo usuário antes desta revisão, mas a nova versão ainda exige nova captura visual no Windows para comprovar o gráfico e as tabelas após a alteração. Vídeo com voz humana, link não listado, repositório GitHub privado, compartilhamento com `fiap-tutoria`, reconciliação documental das User Stories e submissão no AVA são ações externas do grupo, não simuladas pelo software. Nenhuma nota máxima está garantida por testes automáticos.

## Compatibilidade de formatos

SQLite é o banco operacional; o DrawSQL anterior é apenas visualização. Execute migrações em bancos existentes, não o esquema consolidado por cima de um banco populado. O módulo sintético antigo é opcional e separado dos modelos reais; não execute `demo_pipeline` no banco científico de apresentação para criar registros desnecessários.
