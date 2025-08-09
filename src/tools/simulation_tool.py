import logging
from typing import List, Dict, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SimulationInput(BaseModel):
    """Input schema for simulation tool - Enhanced for sales discovery"""
    vehicle_interest: str = Field(..., description="The type of vehicle the user is interested in (e.g., 'carro', 'veiculo', 'onix', 'tracker', etc.)")
    price_range: Optional[str] = Field(None, description="Budget range preference (e.g., 'até 1000', '1000-2000', 'acima de 2000', 'flexivel')")
    usage_purpose: Optional[str] = Field(None, description="How they plan to use the vehicle (e.g., 'trabalho', 'familia', 'primeiro_carro', 'investimento')")
    urgency_level: Optional[str] = Field(None, description="When they need the vehicle (e.g., 'urgente', 'ate_6_meses', 'sem_pressa')")
    current_situation: Optional[str] = Field(None, description="Current transportation situation (e.g., 'sem_carro', 'carro_velho', 'upgrade')")
    family_size: Optional[str] = Field(None, description="Family composition affecting vehicle choice (e.g., 'solteiro', 'casal', 'familia_pequena', 'familia_grande')")


class VehicleSimulationTool(BaseTool):
    """Tool for providing vehicle consortium simulation data"""
    simulation_data: dict = Field(default_factory=dict)

    def __init__(self):
        super().__init__(
            name="vehicle_simulation",
            description="""
                Ferramenta para fornecer simulações de consórcio de veículos com valores de parcelas e prazos.
                Use quando o cliente demonstrar interesse em fazer uma simulação ou quiser conhecer os valores disponíveis.

                Input: tipo de veículo de interesse do cliente
                Output: opções de simulação com valores, prazos e parcelas
                """,
            args_schema=SimulationInput
        )
        self._load_simulation_data()

    def _load_simulation_data(self):
        """Load simulation data"""
        self.simulation_data = {
            "plano_84_meses": [
                {
                    "veiculo": "120% Novo Tracker 1.0 Turbo Premier",
                    "prazo_meses": 84,
                    "valor_credito": 227508.00,
                    "parcela_normal": 3344.93,
                    "parcela_mais_facil": 2682.38
                },
                {
                    "veiculo": "115% Novo Tracker 1.0 Turbo Premier",
                    "prazo_meses": 84,
                    "valor_credito": 218029.00,
                    "parcela_normal": 3205.56,
                    "parcela_mais_facil": 2570.61
                },
                {
                    "veiculo": "110% Novo Tracker 1.0 Turbo Premier",
                    "prazo_meses": 84,
                    "valor_credito": 208549.00,
                    "parcela_normal": 3066.19,
                    "parcela_mais_facil": 2458.85
                },
                {
                    "veiculo": "Novo Tracker 1.0 Turbo Premier",
                    "prazo_meses": 84,
                    "valor_credito": 189590.00,
                    "parcela_normal": 2872.28,
                    "parcela_mais_facil": 2344.39
                },
                {
                    "veiculo": "Tracker Turbo LTZ",
                    "prazo_meses": 84,
                    "valor_credito": 169490.00,
                    "parcela_normal": 2567.76,
                    "parcela_mais_facil": 2095.84
                },
                {
                    "veiculo": "Nova Montana Premier",
                    "prazo_meses": 84,
                    "valor_credito": 168890.00,
                    "parcela_normal": 2558.67,
                    "parcela_mais_facil": 2088.42
                },
                {
                    "veiculo": "Nova Montana LTZ",
                    "prazo_meses": 84,
                    "valor_credito": 160390.00,
                    "parcela_normal": 2429.90,
                    "parcela_mais_facil": 1983.32
                },
                {
                    "veiculo": "Spin Premier",
                    "prazo_meses": 84,
                    "valor_credito": 154990.00,
                    "parcela_normal": 2344.39,
                    "parcela_mais_facil": 1916.54
                },
                {
                    "veiculo": "Nova Montana LT",
                    "prazo_meses": 84,
                    "valor_credito": 145590.00,
                    "parcela_normal": 2205.68,
                    "parcela_mais_facil": 1800.31
                },
                {
                    "veiculo": "Nova Montana 1.2 Turbo",
                    "prazo_meses": 84,
                    "valor_credito": 138290.00,
                    "parcela_normal": 2094.62,
                    "parcela_mais_facil": 1709.93
                },
                {
                    "veiculo": "Onix Turbo Premier",
                    "prazo_meses": 84,
                    "valor_credito": 129190.00,
                    "parcela_normal": 1957.22,
                    "parcela_mais_facil": 1597.22
                },
                {
                    "veiculo": "Novo Tracker Turbo AT",
                    "prazo_meses": 84,
                    "valor_credito": 119900.00,
                    "parcela_normal": 1816.48,
                    "parcela_mais_facil": 1482.64
                },
                {
                    "veiculo": "Onix Plus Turbo LT",
                    "prazo_meses": 84,
                    "valor_credito": 119190.00,
                    "parcela_normal": 1805.02,
                    "parcela_mais_facil": 1473.86
                }
            ],
            "plano_96_meses": [
                {
                    "veiculo": "110% Onix 1.0",
                    "prazo_meses": 96,
                    "valor_credito": 104390.00,
                    "parcela_normal": 1379.74,
                    "parcela_mais_facil": 1131.48
                },
                {
                    "veiculo": "Onix 1.0",
                    "prazo_meses": 96,
                    "valor_credito": 94900.00,
                    "parcela_normal": 1254.31,
                    "parcela_mais_facil": 1028.62
                },
                {
                    "veiculo": "90% Onix 1.0",
                    "prazo_meses": 96,
                    "valor_credito": 85410.00,
                    "parcela_normal": 1128.88,
                    "parcela_mais_facil": 925.76
                },
                {
                    "veiculo": "80% Onix 1.0",
                    "prazo_meses": 96,
                    "valor_credito": 75920.00,
                    "parcela_normal": 1007.74,
                    "parcela_mais_facil": 827.18
                },
                {
                    "veiculo": "75% Onix 1.0",
                    "prazo_meses": 96,
                    "valor_credito": 71176.00,
                    "parcela_normal": 944.77,
                    "parcela_mais_facil": 775.49
                },
                {
                    "veiculo": "65% Onix 1.0",
                    "prazo_meses": 96,
                    "valor_credito": 61686.00,
                    "parcela_normal": 818.80,
                    "parcela_mais_facil": 672.10
                },
                {
                    "veiculo": "60% Onix 1.0",
                    "prazo_meses": 96,
                    "valor_credito": 56940.00,
                    "parcela_normal": 775.10,
                    "parcela_mais_facil": 633.26
                }
            ]
        }

    def _run(self, vehicle_interest: str, price_range: Optional[str] = None,
             usage_purpose: Optional[str] = None, urgency_level: Optional[str] = None,
             current_situation: Optional[str] = None, family_size: Optional[str] = None) -> str:
        """
        Provide strategic vehicle simulation based on sales discovery

        Args:
            vehicle_interest: Type of vehicle the user is interested in
            price_range: Budget range preference
            usage_purpose: How they plan to use the vehicle
            urgency_level: When they need the vehicle
            current_situation: Current transportation situation
            family_size: Family composition

        Returns:
            Strategic simulation response with sales techniques
        """
        try:
            # ✅ Normalize all inputs
            normalized_inputs = {
                'vehicle_interest': self._normalize_input(vehicle_interest),
                'price_range': self._normalize_input(price_range) if price_range else None,
                'usage_purpose': self._normalize_input(usage_purpose) if usage_purpose else None,
                'urgency_level': self._normalize_input(urgency_level) if urgency_level else None,
                'current_situation': self._normalize_input(current_situation) if current_situation else None,
                'family_size': self._normalize_input(family_size) if family_size else None
            }

            # 🎯 Analyze customer profile for strategic presentation
            customer_profile = self._analyze_customer_profile(normalized_inputs)

            # 🚗 Get relevant simulations with strategic filtering
            relevant_simulations = self._get_strategic_simulations(normalized_inputs, customer_profile)

            if not relevant_simulations:
                return self._get_discovery_questions(normalized_inputs)

            return self._format_strategic_response(relevant_simulations, customer_profile, normalized_inputs)

        except Exception as e:
            print(f"🚗 ERROR in simulation tool: {str(e)}")
            logger.error(f"🚗 ERROR in simulation tool: {str(e)}")
            return self._get_fallback_response()

    def _normalize_input(self, input_value) -> str:
        """
        Normalize input to handle various formats from CrewAI.

        Args:
            input_value: Input from CrewAI (can be string, dict, or other)

        Returns:
            str: Normalized input string
        """
        try:
            # Case 1: Already a string
            if isinstance(input_value, str):
                return input_value.strip()

            # Case 2: Dictionary with known keys
            if isinstance(input_value, dict):
                if "description" in input_value:
                    return str(input_value["description"]).strip()
                elif "vehicle_interest" in input_value:
                    return str(input_value["vehicle_interest"]).strip()
                elif "value" in input_value:
                    return str(input_value["value"]).strip()
                # If dict but no known keys, convert to string
                return str(input_value).strip()

            # Case 3: None or empty
            if input_value is None:
                return ""

            # Case 4: Any other type, convert to string
            return str(input_value).strip()

        except Exception as e:
            logger.error(f"Error normalizing input: {e}, input: {input_value}")
            return str(input_value) if input_value is not None else ""

    def _analyze_customer_profile(self, inputs: Dict) -> Dict[str, str]:
        """
        Analyze customer profile for strategic sales approach
        """
        profile = {
            'buyer_type': 'unknown',
            'urgency': 'medium',
            'budget_consciousness': 'medium',
            'decision_style': 'analytical',
            'pain_points': [],
            'motivators': []
        }

        # Analyze urgency
        urgency = inputs.get('urgency_level', '').lower()
        if any(word in urgency for word in ['urgente', 'rapido', 'agora', 'já']):
            profile['urgency'] = 'high'
            profile['motivators'].append('time_pressure')
        elif any(word in urgency for word in ['sem_pressa', 'futuro', 'plano']):
            profile['urgency'] = 'low'
            profile['decision_style'] = 'deliberate'

        # Analyze budget consciousness
        price_range = inputs.get('price_range', '').lower()
        if any(word in price_range for word in ['barato', 'economico', 'baixo', 'até_1000']):
            profile['budget_consciousness'] = 'high'
            profile['pain_points'].append('budget_constraints')
        elif any(word in price_range for word in ['premium', 'alto', 'acima_2000']):
            profile['budget_consciousness'] = 'low'
            profile['motivators'].append('quality_features')

        # Analyze buyer type based on situation
        situation = inputs.get('current_situation', '').lower()
        purpose = inputs.get('usage_purpose', '').lower()

        if any(word in situation for word in ['sem_carro', 'primeiro']):
            profile['buyer_type'] = 'first_time'
            profile['pain_points'].extend(['lack_transportation', 'uncertainty'])
            profile['motivators'].extend(['independence', 'reliability'])
        elif any(word in situation for word in ['carro_velho', 'problemas']):
            profile['buyer_type'] = 'replacement'
            profile['pain_points'].extend(['unreliability', 'maintenance_costs'])
            profile['motivators'].extend(['peace_of_mind', 'cost_savings'])
        elif any(word in situation for word in ['upgrade', 'melhor']):
            profile['buyer_type'] = 'upgrader'
            profile['motivators'].extend(['status', 'better_features'])

        if any(word in purpose for word in ['trabalho', 'renda']):
            profile['motivators'].extend(['income_generation', 'professional_image'])
        elif any(word in purpose for word in ['familia', 'crianca']):
            profile['motivators'].extend(['family_safety', 'comfort'])

        return profile

    def _get_strategic_simulations(self, inputs: Dict, profile: Dict) -> List[Dict]:
        """
        Get simulations strategically filtered based on customer profile
        """
        vehicle_interest = inputs.get('vehicle_interest', '')
        price_range = inputs.get('price_range', '')

        # Base filtering
        all_simulations = self.simulation_data["plano_84_meses"] + self.simulation_data["plano_96_meses"]
        relevant = []

        # Vehicle type filtering
        interest_lower = vehicle_interest.lower()
        for sim in all_simulations:
            vehicle_name = sim["veiculo"].lower()
            if any(keyword in vehicle_name for keyword in [
                interest_lower, "onix" if "onix" in interest_lower else "",
                "tracker" if "tracker" in interest_lower else "",
                "montana" if "montana" in interest_lower else "",
                "spin" if "spin" in interest_lower else ""
            ]):
                relevant.append(sim)

        # Strategic filtering based on profile
        if profile['budget_consciousness'] == 'high':
            # Show cheapest options first
            relevant = sorted(relevant, key=lambda x: x["parcela_mais_facil"])[:4]
        elif profile['urgency'] == 'high':
            # Show mix of affordable and premium for urgency-based decisions
            relevant = sorted(relevant, key=lambda x: x["parcela_mais_facil"])
            # Get 2 cheap + 2 mid-range options
            if len(relevant) > 4:
                relevant = relevant[:2] + relevant[len(relevant)//2:len(relevant)//2+2]
        else:
            # Show balanced options
            relevant = sorted(relevant, key=lambda x: x["parcela_mais_facil"])[:5]

        return relevant if relevant else all_simulations[:3]  # Fallback to top 3

    def _get_discovery_questions(self, inputs: Dict) -> str:
        """
        Return strategic discovery questions when no simulations match
        """
        return """🤔 **Vamos encontrar a opção perfeita para você!**

Para te apresentar as melhores simulações, me conte um pouco mais:

🎯 **Sobre seu interesse:**
• Que tipo de veículo você tem em mente? (Onix, Tracker, Montana...)
• Qual o principal uso? (trabalho, família, primeiro carro...)

💰 **Sobre seu orçamento:**
• Qual faixa de parcela cabe no seu bolso?
• Prefere parcelas menores ou quer quitar mais rápido?

⏰ **Sobre o timing:**
• Para quando você precisa do veículo?
• É urgente ou pode planejar com calma?

Com essas informações, posso te mostrar exatamente as opções que fazem sentido para seu perfil! 🚗✨"""

    def _get_fallback_response(self) -> str:
        """
        Fallback response for errors
        """
        return """🚗 **Estou aqui para te ajudar com sua simulação!**

Tivemos um pequeno problema técnico, mas posso te apresentar nossas principais opções:

**💡 Destaques do momento:**
• Onix 1.0 - A partir de R$ 633/mês (96 meses)
• Tracker - A partir de R$ 1.482/mês (84 meses)
• Montana - A partir de R$ 1.709/mês (84 meses)

**🎯 Me conte qual veículo te interessa** e eu busco as melhores condições para você!

*Todas as opções incluem o Plano Mais Fácil com parcelas reduzidas.* ✨"""

    def _format_strategic_response(self, simulations: List[Dict], profile: Dict, inputs: Dict) -> str:
        """
        Format simulation response using strategic sales techniques
        """
        if not simulations:
            return self._get_discovery_questions(inputs)

        # 🎯 Customize opening based on customer profile
        opening = self._get_strategic_opening(profile, inputs)

        response = f"{opening}\n\n"
        response += "🚗 **Suas Opções Personalizadas:**\n\n"

        # 💡 Present options strategically
        for i, sim in enumerate(simulations[:3], 1):  # Limit to top 3 for focus
            response += self._format_single_option(sim, i, profile)

        # 🔥 Add strategic closing based on profile
        response += self._get_strategic_closing(profile, inputs, simulations)

        return response

    def _get_strategic_opening(self, profile: Dict, inputs: Dict) -> str:
        """
        Generate strategic opening based on customer profile
        """
        buyer_type = profile.get('buyer_type', 'unknown')
        urgency = profile.get('urgency', 'medium')

        if buyer_type == 'first_time':
            return "🎉 **Que momento especial! Seu primeiro veículo próprio está quase aí!**\n\nSelecionei as melhores opções para quem está começando - com parcelas que cabem no bolso e toda a segurança que você merece:"

        elif buyer_type == 'replacement':
            return "🔧 **Chega de dor de cabeça com carro velho!**\n\nVou te mostrar opções que vão te dar tranquilidade total - sem surpresas, sem manutenção cara, só a liberdade de ter um veículo confiável:"

        elif buyer_type == 'upgrader':
            return "⭐ **Hora do upgrade que você merece!**\n\nSelecionei veículos com as melhores tecnologias e conforto - vamos te colocar no patamar que combina com você:"

        elif urgency == 'high':
            return "⚡ **Sei que você precisa resolver isso rápido!**\n\nAqui estão as opções que podem sair mais rapidamente, com as melhores condições disponíveis hoje:"

        else:
            return "🎯 **Perfeito! Analisei seu perfil e trouxe as opções ideais:**\n\nBaseado no que você me contou, essas são as simulações que mais fazem sentido:"

    def _format_single_option(self, sim: Dict, index: int, profile: Dict) -> str:
        """
        Format a single option with strategic emphasis
        """
        option = f"**{index}. {sim['veiculo']}**"

        # Add strategic badges based on profile
        badges = []
        if profile.get('budget_consciousness') == 'high':
            if sim['parcela_mais_facil'] < 1500:
                badges.append("💚 ECONÔMICO")

        if profile.get('urgency') == 'high':
            badges.append("⚡ DISPONÍVEL")

        if sim['parcela_normal'] - sim['parcela_mais_facil'] > 500:
            badges.append("🔥 SUPER ECONOMIA")

        if badges:
            option += f" {' '.join(badges)}"

        option += f"\n💰 Valor do crédito: R$ {sim['valor_credito']:,.2f}\n"
        option += f"📅 {sim['prazo_meses']} meses\n"

        # Strategic presentation of parcels
        savings = sim['parcela_normal'] - sim['parcela_mais_facil']
        option += f"💳 ~~R$ {sim['parcela_normal']:,.2f}~~ → **R$ {sim['parcela_mais_facil']:,.2f}/mês**\n"
        option += f"✨ **Você economiza R$ {savings:,.2f} todo mês!**\n"
        option += f"🎯 Economia total: R$ {(savings * sim['prazo_meses']):,.2f}\n"
        option += "---\n\n"

        return option

    def _get_strategic_closing(self, profile: Dict, inputs: Dict, simulations: List[Dict]) -> str:
        """
        Generate strategic closing to drive action
        """
        urgency = profile.get('urgency', 'medium')
        buyer_type = profile.get('buyer_type', 'unknown')

        if urgency == 'high':
            return """🔥 **ATENÇÃO: Grupos com poucas vagas!**

⏰ **Para garantir sua vaga hoje:**
1. Me fala qual opção mais te chamou atenção
2. Confirmo disponibilidade em tempo real
3. Reservamos sua posição no grupo

**👨‍💼 Posso iniciar sua proposta agora mesmo!** Qual opção você quer conhecer melhor?"""

        elif buyer_type == 'first_time':
            return """🎓 **Seu primeiro consórcio merece atenção especial!**

**Próximos passos:**
✅ Qual dessas opções faz mais sentido para você?
✅ Te explico como funciona todo o processo
✅ Tiro todas suas dúvidas sem compromisso

**💬 Me conta qual opção despertou seu interesse!** Vou te dar todos os detalhes para você decidir com tranquilidade."""

        else:
            return """💎 **Qual dessas opções mais combina com você?**

**🎯 Próximo passo:** Me conta qual veículo despertou seu interesse e eu:
• Mostro mais detalhes da simulação
• Explico as vantagens exclusivas
• Te passo as condições especiais disponíveis

**💬 Qual opção quer conhecer melhor?** Estou aqui para tirar todas suas dúvidas! 🚗✨"""

    # ✅ Legacy methods removed - now using strategic sales approach


# Instance for use in CrewAI
vehicle_simulation_tool = VehicleSimulationTool()
