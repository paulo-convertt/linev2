from typing import Dict, Any
from datetime import datetime

class ConsorcioLeadScoring:
    def __init__(self):
        self.scoring_weights = {
            "renda": 40,          # Peso maior para capacidade financeira
            "profissao": 25,      # Estabilidade profissional
            "estado_civil": 20,   # Estabilidade pessoal
            "dados_completos": 15 # Completude dos dados
        }

    def calculate_score(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        score = 0
        reasons = []

        # 1. Análise de Renda (40 pontos)
        if lead_data["renda"]:
            renda = lead_data.get("renda", "").lower()
            if "5" in renda:
                score += 40
                reasons.append("Renda alta - excelente capacidade de pagamento (40 pts)")
            elif "4" in renda:
                score += 35
                reasons.append("Renda muito boa - boa capacidade de pagamento (35 pts)")
            elif "3" in renda:
                score += 30
                reasons.append("Renda média-alta - capacidade adequada (30 pts)")
            elif "2" in renda:
                score += 20
                reasons.append("Renda média - capacidade limitada (20 pts)")
            else:
                score += 10
                reasons.append("Renda baixa - análise especial necessária (10 pts)")

        if lead_data["profissao"]:
            # 2. Análise de Profissão (25 pontos)
            profissao = lead_data.get("profissao", "").lower()
            profissoes_alta_estabilidade = [
                "servidor", "funcionario publico", "medico", "advogado",
                "engenheiro", "professor", "militar", "policial"
            ]
            profissoes_media_estabilidade = [
                "clt", "empregado", "funcionario", "tecnico", "analista",
                "gerente", "supervisor"
            ]

            if any(prof in profissao for prof in profissoes_alta_estabilidade):
                score += 25
                reasons.append("Profissão de alta estabilidade (25 pts)")
            elif any(prof in profissao for prof in profissoes_media_estabilidade):
                score += 20
                reasons.append("Profissão de média estabilidade (20 pts)")
            elif "autonomo" in profissao or "empresario" in profissao:
                score += 15
                reasons.append("Profissão autônoma - análise de renda necessária (15 pts)")
            else:
                score += 10
                reasons.append("Profissão a ser analisada (10 pts)")

        if lead_data["estado_civil"]:
            # 3. Estado Civil (20 pontos)
            estado_civil = lead_data.get("estado_civil", "").lower()
            if "casado" in estado_civil or "união estável" in estado_civil:
                score += 20
                reasons.append("Estado civil favorável - maior estabilidade (20 pts)")
            elif "solteiro" in estado_civil:
                score += 15
                reasons.append("Solteiro - perfil adequado (15 pts)")
            else:
                score += 10
                reasons.append("Estado civil neutro (10 pts)")

        # 4. Completude dos Dados (15 pontos)
        campos_obrigatorios = [
            "nome", "cpf", "estado_civil", "naturalidade", "endereco",
            "email", "nome_mae", "renda", "profissao"
        ]

        campos_preenchidos = sum(1 for campo in campos_obrigatorios
                               if lead_data.get(campo))
        completude_pct = (campos_preenchidos / len(campos_obrigatorios)) * 100

        if completude_pct == 100:
            score += 15
            reasons.append("Dados 100% completos (15 pts)")
        elif completude_pct >= 80:
            score += 12
            reasons.append("Dados quase completos (12 pts)")
        elif completude_pct >= 60:
            score += 8
            reasons.append("Dados parcialmente completos (8 pts)")
        else:
            score += 5
            reasons.append("Dados incompletos (5 pts)")

        # Classificação
        if score >= 80:
            categoria = "Premium"
            prioridade = "Alta"
            recomendacoes = [
                "Contato imediato da equipe comercial",
                "Apresentar produtos premium",
                "Oferecer condições especiais"
            ]
        elif score >= 60:
            categoria = "Qualificado"
            prioridade = "Média"
            recomendacoes = [
                "Agendar reunião em 24h",
                "Apresentar produtos padrão",
                "Solicitar documentação complementar"
            ]
        else:
            categoria = "Potencial"
            prioridade = "Baixa"
            recomendacoes = [
                "Incluir em campanha de nutrição",
                "Solicitar mais informações financeiras",
                "Aguardar melhor momento"
            ]

        return {
            "score": score,
            "categoria": categoria,
            "prioridade": prioridade,
            "razoes": reasons,
            "recomendacoes": recomendacoes,
            "completude_dados": completude_pct,
            "timestamp": datetime.now().isoformat()
        }
