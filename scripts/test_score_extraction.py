"""Test script to verify score extraction logic."""

import re

# Sample grading task outputs to test
test_outputs = [
    # Format 1: Tool output
    """AVALIAÇÃO REGISTRADA COM SUCESSO
Desenvolvedor: John Doe
Nota Final: 8/10
Motivo: Código bem estruturado, mas faltam alguns testes unitários.""",
    
    # Format 2: With extra text
    """Análise completa do desenvolvedor.

AVALIAÇÃO REGISTRADA COM SUCESSO
Desenvolvedor: Jane Smith
Nota Final: 9/10
Motivo: Excelente qualidade de código, bem documentado e testado.

Fim da análise.""",
    
    # Format 3: Different case
    """avaliação registrada com sucesso
desenvolvedor: Bob Wilson
nota final: 6/10
motivo: Código funcional mas precisa de refatoração."""
]

def test_extraction(output):
    """Test the extraction logic."""
    print(f"\n{'='*60}")
    print("Testing output:")
    print(output[:100] + "..." if len(output) > 100 else output)
    print(f"{'='*60}")
    
    developer_match = re.search(r"Desenvolvedor:\s*(.+?)(?:\n|$)", output, re.IGNORECASE)
    score_match = re.search(r"Nota\s+Final:\s*(\d+)/10", output, re.IGNORECASE)
    justification_match = re.search(r"Motivo:\s*(.+)", output, re.DOTALL | re.IGNORECASE)
    
    if developer_match:
        print(f"✓ Developer: {developer_match.group(1).strip()}")
    else:
        print("✗ Developer: NOT FOUND")
    
    if score_match:
        print(f"✓ Score: {score_match.group(1)}/10")
    else:
        print("✗ Score: NOT FOUND")
    
    if justification_match:
        justification = justification_match.group(1).strip()
        print(f"✓ Justification: {justification[:50]}...")
    else:
        print("✗ Justification: NOT FOUND")
    
    return bool(developer_match and score_match)

if __name__ == "__main__":
    print("Testing Score Extraction Logic")
    print("="*60)
    
    results = []
    for i, output in enumerate(test_outputs, 1):
        success = test_extraction(output)
        results.append(success)
    
    print(f"\n{'='*60}")
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print(f"{'='*60}")
