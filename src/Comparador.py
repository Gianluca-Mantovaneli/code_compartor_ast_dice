"""
Comparador Híbrido de Código - Dice + AST
"""
import ast
import re
import os
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
    def _extract_ast_metrics(tree: ast.AST) -> Dict:
        metrics = {
            'nodes_count': 0,
            'structure': [],
            'complexity': 0  # Ciclo de caminhos
        }
        for node in ast.walk(tree):
            metrics['nodes_count'] += 1
            # Registra a sequência de tipos de nós para comparar a "assinatura" do código
            metrics['structure'].append(type(node).__name__)

            if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                metrics['complexity'] += 1
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


class CodeAnalyzer(CodeComparator):
    """Analisa a complexidade e saúde de um único arquivo de código"""

    def analyze(self, code: str) -> dict:
        try:
            tree = ast.parse(code)
            metrics = self._extract_ast_metrics(tree)

            # Cálculo de Complexidade Ciclomática simplificado:
            # Base 1 + cada ponto de decisão (if, for, while, with, assert, except)
            complexity = 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.And, ast.Or, ast.ExceptHandler)):
                    complexity += 1

            return {
                "complexidade_ciclomatica": complexity,
                "total_funcoes": metrics['functions'],
                "total_classes": metrics['classes'],
                "linhas_totais": len(code.splitlines())
            }
        except SyntaxError:
            return {"erro": "Falha ao processar código (Syntax Error)"}

    def print_analysis(self, results: dict):
        print(f"\n{Fore.MAGENTA}--- ANÁLISE DE COMPLEXIDADE ---")
        if "erro" in results:
            print(f"{Fore.RED}{results['erro']}")
            return

        comp = results['complexidade_ciclomatica']
        # Escala de risco baseada em padrões de engenharia de software
        color = Fore.GREEN if comp <= 10 else Fore.YELLOW if comp <= 20 else Fore.RED

        print(f"Complexidade Ciclomática: {color}{comp}")
        print(f"{Fore.WHITE}Status: {self._get_complexity_status(comp)}")
        print(f"Total de Funções: {results['total_funcoes']}")
        print(f"Total de Classes: {results['classes']}")
        print(f"Linhas de Código: {results['linhas_totais']}")

    @staticmethod
    def _get_complexity_status(n):
        if n <= 10: return "Código Simples (Baixo Risco)"
        if n <= 20: return "Código Moderado"
        if n <= 50: return "Código Complexo (Alto Risco)"
        return "Código Muito Instável / Difícil de Testar"

    def analyze_directory(self, path: str):
        """Percorre um diretório e analisa todos os arquivos de código"""
        total_files = 0
        aggregate_results = {
            "complexidade_acumulada": 0,
            "total_funcoes": 0,
            "total_classes": 0,
            "total_linhas": 0,
            "arquivos_analisados": []
        }

        # Percorre a pasta e subpastas
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            code = f.read()

                        # Usa o analyze que criamos antes
                        res = self.analyze(code)

                        if "erro" not in res:
                            total_files += 1
                            aggregate_results["complexidade_acumulada"] += res["complexidade_ciclomatica"]
                            aggregate_results["total_funcoes"] += res["total_funcoes"]
                            aggregate_results["total_classes"] += res["total_classes"]
                            aggregate_results["total_linhas"] += res["linhas_totais"]
                            aggregate_results["arquivos_analisados"].append((file, res["complexidade_ciclomatica"]))
                    except Exception as e:
                        print(f"{Fore.RED}Erro ao ler {file}: {e}")

        self._print_directory_report(aggregate_results, total_files)

    @staticmethod
    def _print_directory_report(data, count):
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW} ESTIMATIVA DE CÓDIGO GERADO (PROJETO COMPLETO)")
        print(f"{Fore.CYAN}{'=' * 60}")

        if count == 0:
            print(f"{Fore.RED}Nenhum arquivo encontrado no diretório.")
            return

        print(f"{Fore.LIGHTWHITE_EX}Arquivos Processados : {count}")
        print(f"Total de Linhas      : {data['total_linhas']}")
        print(f"Total de Classes     : {data['total_classes']}")
        print(f"Total de Funções     : {data['total_funcoes']}")
        print(f"Média de Complexidade: {data['complexidade_acumulada'] / count:.2f}")

        print(f"\n{Fore.LIGHTMAGENTA_EX}Top Arquivos mais Complexos:")
        # Ordena os arquivos pela complexidade
        sorted_files = sorted(data['arquivos_analisados'], key=lambda x: x[1], reverse=True)
        for name, comp in sorted_files[:5]:
            print(f"  - {name}: {comp}")
        print(f"{Fore.CYAN}{'=' * 60}\n")

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
            try:
                file1 = input(f"{Fore.GREEN}Caminho do primeiro arquivo: ").strip()
                file2 = input(f"{Fore.GREEN}Caminho do segundo arquivo: ").strip()
                compare_directories(comparator,file1, file2)
            except Exception as e:
                print(f"{Fore.RED}Erro: {e}")

        elif choice == '4':
            path = input(f"{Fore.GREEN}Digite o caminho da pasta do projeto: ").strip()
            if os.path.exists(path):
                analyzer = CodeAnalyzer()
                analyzer.analyze_directory(path)
            else:
                print(f"{Fore.RED}Caminho não encontrado!")

        elif choice == '0':
            print(f"{Fore.GREEN}Até logo!")
            break

        else:
            print(f"{Fore.RED}Opção inválida!")


def compare_directories(self, path1: str, path2: str):
    files1 = {f for f in os.listdir(path1) if f.endswith('.java')}
    files2 = {f for f in os.listdir(path2) if f.endswith('.java')}

    common = files1 & files2
    for file in common:
        res = self.compare_files(os.path.join(path1, file), os.path.join(path2, file))
        print(f"Arquivo {file}: {res.final_score:.2%}")

if __name__ == "__main__":
    main()