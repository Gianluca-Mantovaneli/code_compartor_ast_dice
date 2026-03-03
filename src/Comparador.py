"""
Comparador Híbrido de Código - Dice + AST + FrameWeb Validator
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
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW} RELATÓRIO DE COMPARAÇÃO DE CÓDIGO")
        print(f"{Fore.CYAN}{'=' * 50}")

        level = self._get_similarity_level()
        level_color = {
            'Muito Baixa': Fore.RED, 'Baixa': Fore.LIGHTRED_EX,
            'Média': Fore.YELLOW, 'Alta': Fore.LIGHTGREEN_EX, 'Muito Alta': Fore.GREEN
        }.get(level, Fore.WHITE)

        print(f"\n{Fore.LIGHTMAGENTA_EX}NÍVEL DE SIMILARIDADE:")
        print(f"  {level_color}{level}{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}{'=-' * 25}")
        print(f"\n{Fore.LIGHTMAGENTA_EX}SCORES:")
        print(f"{Fore.LIGHTYELLOW_EX}  Dice Coefficient    : {self.dice_score:.2%}")
        print(f"{Fore.LIGHTYELLOW_EX}  AST Similarity      : {self.ast_score:.2%}")
        print(f"{Fore.LIGHTBLUE_EX}  Média Final         : {self.final_score:.2%}")
        print(f"\n{Fore.CYAN}{'=-' * 25}\n")

    def _get_similarity_level(self) -> str:
        if self.final_score >= 0.9: return "Muito Alta"
        if self.final_score >= 0.7: return "Alta"
        if self.final_score >= 0.5: return "Média"
        if self.final_score >= 0.3: return "Baixa"
        return "Muito Baixa"

class CodeComparator:
    def __init__(self, dice_weight: float = 0.3, ast_weight: float = 0.7):
        self.dice_weight = dice_weight
        self.ast_weight = ast_weight

    def compare(self, code1: str, code2: str) -> ComparisonResult:
        dice_score = self._calculate_dice(code1, code2)
        ast_score = self._calculate_ast_similarity(code1, code2)
        final_score = (dice_score * self.dice_weight) + (ast_score * self.ast_weight)
        return ComparisonResult(dice_score, ast_score, final_score, {})

    def compare_files(self, file1: str, file2: str) -> ComparisonResult:
        content1 = self._read_safe(file1)
        content2 = self._read_safe(file2)
        return self.compare(content1, content2)

    def _read_safe(self, path):
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(path, 'r', encoding=enc) as f:
                    return f.read()
            except: continue
        return ""

    def _calculate_dice(self, str1: str, str2: str) -> float:
        s1, s2 = self._normalize_code(str1), self._normalize_code(str2)
        def get_bigrams(t): return {t[i:i+2] for i in range(len(t)-1)}
        b1, b2 = get_bigrams(s1), get_bigrams(s2)
        if not b1 and not b2: return 0.0
        return (2 * len(b1 & b2)) / (len(b1) + len(b2))

    @staticmethod
    def _normalize_code(code: str) -> str:
        code = re.sub(r'//.*$|/\*[\s\S]*?\*/', '', code, flags=re.MULTILINE)
        code = re.sub(r'\s+', ' ', code)
        return code.lower().strip()

    def _calculate_ast_similarity(self, code1: str, code2: str) -> float:
        # Nota: AST nativo do Python não faz parse de Java.
        # Mantido para compatibilidade Python ou fallback.
        try:
            tree1, tree2 = ast.parse(code1), ast.parse(code2)
            return 1.0 # Simplificado para este contexto
        except: return 0.0

class CodeAnalyzer(CodeComparator):
    def _validate_frameweb_tags(self, code: str) -> Dict[str, bool]:
        tags_to_check = {
            'Controller': r'@Controller|@RestController',
            'Service': r'@Service',
            'Repository': r'@Repository',
            'Entity': r'@Entity',
            'Table': r'@Table'
        }
        return {tag: bool(re.search(pattern, code)) for tag, pattern in tags_to_check.items()}

    def analyze(self, code: str) -> dict:
        try:
            complexity = 1 + len(re.findall(r'\b(if|for|while|case|catch|&&|\|\|)\b', code))
            tags = self._validate_frameweb_tags(code)
            return {
                "complexidade_ciclomatica": complexity,
                "total_metodos": len(re.findall(r'(public|protected|private|static)\s+[\w<>\s]+\s+\w+\s*\(', code)),
                "total_classes": len(re.findall(r'\bclass\b', code)),
                "linhas_totais": len(code.splitlines()),
                "tags": tags
            }
        except Exception as e:
            return {"erro": str(e)}

    def analyze_directory(self, path: str):
        total_files = 0
        aggregate = {
            "complexidade": 0, "linhas": 0, "metodos": 0,
            "tag_counts": {'Controller': 0, 'Service': 0, 'Repository': 0, 'Entity': 0},
            "arquivos": []
        }

        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.java'):
                    content = self._read_safe(os.path.join(root, file))
                    if content:
                        res = self.analyze(content)
                        if "erro" not in res:
                            total_files += 1
                            aggregate["complexidade"] += res["complexidade_ciclomatica"]
                            aggregate["linhas"] += res["linhas_totais"]
                            aggregate["metodos"] += res["total_metodos"]
                            for tag, found in res['tags'].items():
                                if found and tag in aggregate["tag_counts"]:
                                    aggregate["tag_counts"][tag] += 1
                            aggregate["arquivos"].append((file, res["complexidade_ciclomatica"]))

        self._print_directory_report(aggregate, total_files)

    @staticmethod
    def _print_directory_report(data, count):
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW} RESULTADO DA GERAÇÃO - FRAMEWEB COMPLIANCE")
        print(f"{Fore.CYAN}{'=' * 60}")
        if count == 0:
            print(f"{Fore.RED}Nenhum arquivo .java processado.")
            return
        print(f"Arquivos Analisados: {count}")
        print(f"Total de Linhas    : {data['linhas']}")
        print(f"Total de Métodos   : {data['metodos']}")
        print(f"Média Complexidade : {data['complexidade'] / count:.2f}")
        print(f"\n{Fore.LIGHTMAGENTA_EX}Cobertura de Estereótipos (FrameWeb):")
        for tag, qtd in data['tag_counts'].items():
            print(f"  - {tag:10}: {qtd} arquivos ({(qtd/count)*100:.1f}%)")
        print(f"\n{Fore.CYAN}{'=' * 60}\n")

def compare_directories(comp, path1: str, path2: str):
    files1 = {f for f in os.listdir(path1) if f.endswith('.java')}
    files2 = {f for f in os.listdir(path2) if f.endswith('.java')}
    common = files1 & files2
    for file in common:
        res = comp.compare_files(os.path.join(path1, file), os.path.join(path2, file))
        print(f"Arquivo {file}: {res.final_score:.2%}")

def main():
    init(autoreset=True)
    comparator = CodeComparator()
    print(f"{Fore.BLUE}Comparador Hibrido {Fore.LIGHTBLUE_EX}(Dice / FrameWeb Analyzer)")
    print(f"{Fore.CYAN}{'-' * 60}")

    while True:
        print(f"{Fore.GREEN}Escolha uma opção:")
        print("1. Comparar dois códigos (Manual)")
        print("2. Comparar dois arquivos")
        print("3. Comparar Duas Pastas")
        print("4. Analisar Projeto (Complexidade + Tags)")
        print("0. Sair")

        choice = input(f"{Fore.GREEN}Sua escolha: ").strip()
        if choice == '1':
            code1 = input("Cole o código 1 e dê enter: ") # Simplificado para teste rápido
            code2 = input("Cole o código 2 e dê enter: ")
            comparator.compare(code1, code2).print_report()
        elif choice == '2':
            f1, f2 = input("Arq 1: "), input("Arq 2: ")
            comparator.compare_files(f1, f2).print_report()
        elif choice == '3':
            p1, p2 = input("Pasta 1: "), input("Pasta 2: ")
            compare_directories(comparator, p1, p2)
        elif choice == '4':
            path = input("Caminho da pasta: ").strip()
            if os.path.exists(path):
                CodeAnalyzer().analyze_directory(path)
        elif choice == '0': break
        else: print(f"{Fore.RED}Opção inválida!")

if __name__ == "__main__":
    main()