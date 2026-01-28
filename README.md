# Introdução
Este programa foi feito no intuito de comparar códigos que foram feitos a mão com códigos que foram gerados pela ferramenta 
do frameweb. Essa ferramenta utiliza de freemark e dos diagramas uml para gerar tal código. Por isso os diagramas precisam 
estar em sintonia para que o código gerado seja coerente. Esse código primeiro faz uma limpeza no código, tirando comentarios ou espaços,
depois ele faz diferentes comparações, a primeira é usando o **dice-coeficient** que separa as palavras em bigramas (JAVA - JA | AV | VA) 
e calcula com base na seguinte formula $D = \frac{2 \cdot |X \cap Y|}{|X| + |Y|}$. Além disso, é feita uma segunda comparação 
utilizando o método AST, que cria uma arvore dos componetes principais do código *(if, loop, returns, chamadas de função)*. 
O código junta essas duas analises em uma só com pesos 30/70 para o DICE e AST respectivamente, fiz assim porque julguei que a estrutura
do código é mais importante do que os nomes usados nas variaveis.

# Como Usar
O código foi feito em python, portanto precisa-se ter o python mais recente instalado na maquina, além disso foram utilizadas as 
seguintes bibliotecas:
- **Colorama** (Muda cor das mensagens no terminal)

Se preferir pode apenas utilizar o comando `pip install -r requirements.txt`