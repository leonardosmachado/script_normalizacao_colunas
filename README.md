# script_normalizacao_colunas
 It is a script that identifies the column count pattern of a CSV file and uses this to detect malformed rows, concatenating those with more columns than the mode and padding those with fewer columns than the mode with empty spaces.

#1.Leitura
 Lê um arquivo CSV utilizando encoding 'latin1' e identfica se o arquivo possui cabeçalho.

#2.Perfil das Colunas
 Identifica o perfil de cada coluna de acordo com o tipo de dado preenchido e os padrões de cada coluna, por exemplo se uma coluna está comumente vazia no dataset.

#3.Função pontuação
 Indica o quanto a linha candidata é compatível com o perfil, pontuando de acordo com o padrão dos dados considerados já corretos no dataset.

#4.Gerar Linhas candidatas
 Gera linhas candidatas de acordo com o excesso ou falta de colunas relacionadas ao padrão definido em #1.Leitura e #2.Perfil das Colunas.

#5.Processar Linhas
 Processa as linhas candidatas selecionadas no processo anterior, concatenando para o excesso de colunas e adicionando valores nulos as colunas corretas nas linhas faltantes.

#6.Salvar Resultados
 Um novo arquivo CSV é gerado com as correções realizadas juntamente a um arquivo log_eventos.txt que registra todas as alterações feitas.
