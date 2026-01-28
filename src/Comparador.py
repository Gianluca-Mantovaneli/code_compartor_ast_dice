"""
Comparador Híbrido de Código - Dice + AST
"""
import ast
import re
from dataclasses import dataclass
from typing import Dict

from colorama import init, Fore, Style

# Inicializa cores para Windows/Linux/Mac
init(autoreset=True)

@dataclass
class ComparisonResult:
    """Resultado da comparação"""
    dice_score: float
    ast_score: float
    final_score: float
    details: Dict

    def print_report(self):
        """Imprimindo o relatório"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW} RELATÓRIO DE COMPARAÇÃO DE CÓDIGO")
        print(f"{Fore.CYAN}{'=' * 50}")

        # Nível de similaridade
        level = self._get_similarity_level()
        level_color = {
            'Muito Baixa': Fore.RED,
            'Baixa': Fore.LIGHTRED_EX,
            'Média': Fore.YELLOW,
            'Alta': Fore.LIGHTGREEN_EX,
            'Muito Alta': Fore.GREEN
        }.get(level, Fore.WHITE)

        print(f"\n{Fore.LIGHTMAGENTA_EX}NÍVEL DE SIMILARIDADE:")
        print(f"  {level_color}{level}{Style.RESET_ALL}")

        print(f"\n{Fore.CYAN}{'=-' * 25}")

        # Informações
        print(f"\n{Fore.LIGHTMAGENTA_EX}SCORES:")
        print(f"{Fore.LIGHTYELLOW_EX}  Dice Coefficient    : {self.dice_score:.2%}")
        print(f"{Fore.LIGHTYELLOW_EX}  AST Similarity      : {self.ast_score:.2%}")
        print(f"{Fore.LIGHTBLUE_EX}  Média Final         : {self.final_score:.2%}")
        if self.details:
            for key, value in self.details.items():
                if isinstance(value, (int, float)):
                    print(f"{Fore.LIGHTYELLOW_EX}  {key}: {value}")
                elif isinstance(value, list):
                    print(f"  {key}: {', '.join(map(str, value[:3]))}")

        print(f"\n{Fore.CYAN}{'=-' * 25}\n")

    def _get_similarity_level(self) -> str:
        """Determina nível baseado no score final"""
        if self.final_score >= 0.9:
            return "Muito Alta"
        elif self.final_score >= 0.7:
            return "Alta"
        elif self.final_score >= 0.5:
            return "Média"
        elif self.final_score >= 0.3:
            return "Baixa"
        else:
            return "Muito Baixa"

class CodeComparator:
    """
    Comparador que combina Dice Coefficient e AST
    """

    def __init__(self, dice_weight: float = 0.3, ast_weight: float = 0.7):
        """
        Args:
            dice_weight: Peso para Dice Coefficient (0-1)
            ast_weight: Peso para AST Similarity (0-1)
        """
        self.dice_weight = dice_weight
        self.ast_weight = ast_weight

    def compare(self, code1: str, code2: str) -> ComparisonResult:
        """
        Compara dois códigos e retorna resultado

        Args:
            code1: Primeiro código
            code2: Segundo código

        Returns:
            ComparisonResult com análise completa
        """
        # 1. Calcula Dice Coefficient
        dice_score = self._calculate_dice(code1, code2)

        # 2. Calcula AST Similarity
        ast_score = self._calculate_ast_similarity(code1, code2)

        # 3. Score Final (ponderado)
        final_score = (dice_score * self.dice_weight) + (ast_score * self.ast_weight)

        # 4. Coleta detalhes
        details = self._collect_details(code1, code2)

        return ComparisonResult(
            dice_score=dice_score,
            ast_score=ast_score,
            final_score=final_score,
            details=details
        )

    def compare_files(self, file1: str, file2: str) -> ComparisonResult:
        """
        Compara dois arquivos de código

        Args:
            file1: Caminho do primeiro arquivo
            file2: Caminho do segundo arquivo

        Returns:
            ComparisonResult
        """
        try:
            with open(file1, 'r', encoding='utf-8') as f:
                code1 = f.read()
        except:
            code1 = f"# Erro ao ler arquivo: {file1}"

        try:
            with open(file2, 'r', encoding='utf-8') as f:
                code2 = f.read()
        except:
            code2 = f"# Erro ao ler arquivo: {file2}"

        return self.compare(code1, code2)

    def _calculate_dice(self, str1: str, str2: str) -> float:
        """Calcula Dice Coefficient simplificado"""
        # Normaliza código
        str1 = self._normalize_code(str1)
        str2 = self._normalize_code(str2)

        # Gera bigramas
        def get_bigrams(text: str) -> set:
            """Retorna conjunto de bigramas"""
            return {text[i:i + 2] for i in range(len(text) - 1)}

        bigrams1 = get_bigrams(str1)
        bigrams2 = get_bigrams(str2)

        # Calcula Dice
        if not bigrams1 and not bigrams2:
            return 0.0

        intersection = len(bigrams1 & bigrams2)
        return (2 * intersection) / (len(bigrams1) + len(bigrams2))

    @staticmethod
    def _normalize_code(code: str) -> str:
        """Normaliza código para comparação"""
        # Remove comentários
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'\"\"\"[\s\S]*?\"\"\"', '', code)
        code = re.sub(r"\'\'\'[\s\S]*?\'\'\'", '', code)

        # Remove espaços extras
        code = re.sub(r'\s+', ' ', code)

        # Remove espaços desnecessários em torno de operadores
        code = re.sub(r'\s*([=+\-*/%&|^<>!(){}\[\];:,.])\s*', r'\1', code)

        return code.lower().strip()

    def _calculate_ast_similarity(self, code1: str, code2: str) -> float:
        """Calcula similaridade baseada em AST"""
        try:
            # Tenta fazer parse
            tree1 = ast.parse(code1)
            tree2 = ast.parse(code2)

            # Extrai métricas básicas
            metrics1 = self._extract_ast_metrics(tree1)
            metrics2 = self._extract_ast_metrics(tree2)

            # Calcula similaridade entre métricas
            return self._compare_ast_metrics(metrics1, metrics2)

        except SyntaxError:
            # Se não conseguir fazer parse, retorna 0
            return 0.0

    @staticmethod
    def _extract_ast_metrics(tree: ast.AST) -> Dict[str, int]:
        """Extrai métricas básicas da AST"""
        metrics = {
            'functions': 0,
            'classes': 0,
            'imports': 0,
            'if_statements': 0,
            'loops': 0,
            'returns': 0,
            'assignments': 0,
            'calls': 0
        }

        # Visitor simples
        for node in ast.walk(tree):
            node_type = type(node).__name__

            if node_type == 'FunctionDef':
                metrics['functions'] += 1
            elif node_type == 'ClassDef':
                metrics['classes'] += 1
            elif node_type in ['Import', 'ImportFrom']:
                metrics['imports'] += 1
            elif node_type == 'If':
                metrics['if_statements'] += 1
            elif node_type in ['For', 'While']:
                metrics['loops'] += 1
            elif node_type == 'Return':
                metrics['returns'] += 1
            elif node_type in ['Assign', 'AugAssign']:
                metrics['assignments'] += 1
            elif node_type == 'Call':
                metrics['calls'] += 1

        return metrics

    @staticmethod
    def _compare_ast_metrics(m1: Dict, m2: Dict) -> float:
        """Compara métricas AST"""
        total_diff = 0
        total_max = 0

        for key in m1.keys():
            val1 = m1[key]
            val2 = m2[key]
            max_val = max(val1, val2, 1)  # Evita divisão por zero

            diff = abs(val1 - val2) / max_val
            total_diff += diff
            total_max += 1

        # Similaridade = 1 - diferença média
        similarity = 1 - (total_diff / total_max)
        return max(0.0, min(1.0, similarity))

    @staticmethod
    def _collect_details(code1: str, code2: str) -> Dict:
        """Coleta detalhes extras para a tabela"""
        return {
            f'Tamanho do Código A ': len(code1) ,
            'Tamanho do Codigo B ': len(code2),
            'Diferenca Tamanho   ': abs(len(code1) - len(code2))
        }


def main():
    """Função principal para testes"""
    # Cria comparador
    comparator = CodeComparator()

    # Menu interativo
    print(f"{Fore.BLUE}Comparador Hibrido {Fore.LIGHTBLUE_EX}(dice coeficiente / AST)")
    print(f"{Fore.CYAN}{'-' * 60}")

    while True:
        print(f"{Fore.GREEN}Escolha uma opção:")
        print("1. Comparar dois códigos digitados")
        print("2. Comparar dois arquivos")
        print("3. Comparar Duas Pastas (Precisa Implementar)")
        print("4. Sair")

        choice = input(f"{Fore.GREEN}Sua escolha (1-4): ").strip()

        if choice == '1':
            print(f"\n{Fore.GREEN}Digite o primeiro código (finalize com linha em branco):")
            lines1 = []
            while True:
                line = input()
                if not line:
                    break
                lines1.append(line)
            code1 = '\n'.join(lines1)

            print(f"\n{Fore.GREEN}Digite o segundo código (finalize com linha em branco):")
            lines2 = []
            while True:
                line = input()
                if not line:
                    break
                lines2.append(line)
            code2 = '\n'.join(lines2)

            result = comparator.compare(code1, code2)
            result.print_report()

        elif choice == '2':
            file1 = input(f"{Fore.GREEN}Caminho do primeiro arquivo: ").strip()
            file2 = input(f"{Fore.GREEN}Caminho do segundo arquivo: ").strip()

            try:
                result = comparator.compare_files(file1, file2)
                result.print_report()
            except Exception as e:
                print(f"{Fore.RED}Erro: {e}")

        elif choice == '3':
            print("work in progress!!")

        elif choice == '4':
            print(f"{Fore.GREEN}Até logo!")
            break

        else:
            print(f"{Fore.RED}Opção inválida!")


if __name__ == "__main__":
    main()