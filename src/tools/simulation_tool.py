import logging
from typing import List, Dict, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SimulationInput(BaseModel):
    """Input schema for simulation tool"""
    vehicle_interest: str = Field(..., description="The type of vehicle the user is interested in (e.g., 'carro', 'veiculo', 'onix', 'tracker', etc.)")
    price_range: Optional[str] = Field(None, description="Optional price range preference (e.g., 'barato', 'intermediario', 'premium')")

class VehicleSimulationTool(BaseTool):
    """Tool for providing vehicle consortium simulation data"""
    simulation_data: dict = Field(default_factory=dict)

    def __init__(self):
        super().__init__(
            name="vehicle_simulation",
            description="Vehicle consortium simulation tool. Provides installment values and terms. Use when client shows interest in simulations or wants to know available values.",
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

    def _run(self, vehicle_interest: str, price_range: Optional[str] = None) -> str:
        """
        Provide vehicle simulation options based on user interest

        Args:
            vehicle_interest: Type of vehicle the user is interested in
            price_range: Optional price range preference

        Returns:
            Formatted simulation options
        """
        try:
            # ✅ ROBUSTA: Normalize inputs to handle CrewAI variations
            normalized_vehicle_interest = self._normalize_input(vehicle_interest)
            normalized_price_range = self._normalize_input(price_range) if price_range else None

            # Filter simulations based on vehicle interest
            relevant_simulations = self._filter_simulations(normalized_vehicle_interest, normalized_price_range)

            if not relevant_simulations:
                return self._get_all_options_summary()

            return self._format_simulation_response(relevant_simulations)

        except Exception as e:
            print(f"🚗 ERROR in simulation tool: {str(e)}")
            logger.error(f"🚗 ERROR in simulation tool: {str(e)}")
            return f"Erro ao buscar simulações: {str(e)}"

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

    def _filter_simulations(self, vehicle_interest: str, price_range: Optional[str] = None) -> List[Dict]:
        """Filter simulations based on user preferences"""
        all_simulations = self.simulation_data["plano_84_meses"] + self.simulation_data["plano_96_meses"]
        relevant = []

        # Keywords for filtering
        interest_lower = vehicle_interest.lower()

        for sim in all_simulations:
            vehicle_name = sim["veiculo"].lower()

            # Check if vehicle matches interest
            if any(keyword in vehicle_name for keyword in [
                interest_lower, "onix" if "onix" in interest_lower else "",
                "tracker" if "tracker" in interest_lower else "",
                "montana" if "montana" in interest_lower else "",
                "spin" if "spin" in interest_lower else ""
            ]):
                relevant.append(sim)

        # Apply price range filter if specified
        if price_range and relevant:
            if price_range.lower() in ["barato", "economico", "baixo"]:
                relevant = sorted(relevant, key=lambda x: x["parcela_mais_facil"])[:3]
            elif price_range.lower() in ["premium", "alto", "caro"]:
                relevant = sorted(relevant, key=lambda x: x["parcela_mais_facil"], reverse=True)[:3]
            else:  # intermediario
                relevant = sorted(relevant, key=lambda x: x["parcela_mais_facil"])[1:4]

        return relevant[:5]  # Limit to 5 results

    def _format_simulation_response(self, simulations: List[Dict]) -> str:
        """Format simulation results for user display"""
        if not simulations:
            return "Não encontrei simulações específicas para sua preferência."

        response = "🚗 **Simulações Disponíveis:**\n\n"

        for i, sim in enumerate(simulations, 1):
            response += f"**{i}. {sim['veiculo']}**\n"
            response += f"💰 Valor do crédito: R$ {sim['valor_credito']:,.2f}\n"
            response += f"📅 Prazo: {sim['prazo_meses']} meses\n"
            response += f"💳 Parcela normal: R$ {sim['parcela_normal']:,.2f}\n"
            response += f"✨ Parcela Mais Fácil: R$ {sim['parcela_mais_facil']:,.2f}\n"
            response += f"💡 Economia: R$ {(sim['parcela_normal'] - sim['parcela_mais_facil']):,.2f}/mês\n"
            response += "---\n\n"

        response += "🎯 **Qual opção mais te interessa?** Posso te ajudar com mais detalhes ou iniciar sua simulação personalizada!"

        return response

    def _get_all_options_summary(self) -> str:
        """Provide summary of all available options"""
        return """🚗 **Opções de Consórcio Disponíveis:**

**Plano 84 meses (500 participantes):**
• Tracker (várias versões) - a partir de R$ 1.482,64/mês
• Montana (várias versões) - a partir de R$ 1.709,93/mês
• Onix (versões turbo) - a partir de R$ 1.473,86/mês
• Spin Premier - R$ 1.916,54/mês

**Plano 96 meses (999 participantes):**
• Onix 1.0 (várias porcentagens) - a partir de R$ 633,26/mês
• Opções de 60% a 110% do valor - maior flexibilidade

💡 **Qual tipo de veículo te interessa mais?**
Tracker, Montana, Onix ou Spin?

Assim posso te mostrar as melhores opções! 🎯"""


# Instance for use in CrewAI
vehicle_simulation_tool = VehicleSimulationTool()
