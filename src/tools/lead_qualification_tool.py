from typing import Dict, List, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import re
import logging

logger = logging.getLogger(__name__)


class LeadQualificationInput(BaseModel):
    """Input schema for lead qualification tool"""
    current_step: str = Field(..., description="Current qualification step (q1-q18)")
    user_response: str = Field(..., description="User's response to the current question")
    lead_data: Optional[Dict] = Field(default_factory=dict, description="Previously collected lead data")


class LeadQualificationTool(BaseTool):
    """Tool for conducting lead qualification following the structured flow"""

    name: str = "lead_qualification"
    description: str = "Lead qualification tool. Conducts structured qualification flow. Use when client shows interest in simulation or closing deal."
    args_schema: type[BaseModel] = LeadQualificationInput
    questions: dict = Field(default_factory=dict)

    def __init__(self):
        super().__init__(
            name="lead_qualification",
            description="Lead qualification tool. Conducts structured qualification flow with step-by-step questions. Use when client shows interest in simulation or closing deal.",
            args_schema=LeadQualificationInput
        )
        self._load_qualification_flow()

    def _load_qualification_flow(self):
        """Load the qualification questions and validation rules"""
        self.questions = {
            "q1": {
                "id": "nome",
                "question": "Pra começar, me diz seu **nome completo**? É só pra eu registrar seu atendimento certinho.",
                "validation": "mín. 2 palavras",
                "on_error": "Pode me confirmar seu **nome completo** (nome e sobrenome)?"
            },
            "q2": {
                "id": "cpf",
                "question": "Perfeito, obrigado! Agora, seu **CPF** (somente números), por favor. Uso só pra garantir seu cadastro sem duplicidade.",
                "validation": "11 dígitos + DV válido",
                "on_error": "Hum, não reconheci. Me envia o **CPF** com 11 números, sem pontos ou traços?"
            },
            "q3": {
                "id": "estado_civil",
                "question": "Show! Qual seu **estado civil**? 1️⃣ Solteiro(a) | 2️⃣ Casado(a) | 3️⃣ Divorciado(a) | 4️⃣ Viúvo(a) | 5️⃣ União estável",
                "options": ["1", "2", "3", "4", "5"],
                "map": {"1": "Solteiro(a)", "2": "Casado(a)", "3": "Divorciado(a)", "4": "Viúvo(a)", "5": "União estável"},
                "on_error": "Me manda um número de 1 a 5, por favor? Ex.: 2 = Casado(a)."
            },
            "q4": {
                "id": "naturalidade",
                "question": "Obrigada! Qual sua **naturalidade** (cidade/UF onde nasceu)?",
                "validation": "texto contendo cidade e UF (2 letras)",
                "on_error": "Pode enviar no formato **Cidade/UF**? Ex.: Campinas/SP."
            },
            "q5": {
                "id": "endereco_rua",
                "question": "Agora seu **endereço**: qual a **rua/avenida**?",
                "validation": "mín. 3 caracteres",
                "on_error": "Qual o nome da **rua/avenida**?"
            },
            "q6": {
                "id": "endereco_numero",
                "question": "Número, por favor. Se não tiver, pode colocar **S/N**.",
                "validation": "número ou 'S/N'",
                "on_error": "Me diga o **número** da residência (ou S/N)."
            },
            "q7": {
                "id": "endereco_bairro",
                "question": "Bairro:",
                "validation": "mín. 2 caracteres",
                "on_error": "Qual o **bairro**, por favor?"
            },
            "q8": {
                "id": "endereco_cidade",
                "question": "Cidade:",
                "validation": "mín. 2 caracteres",
                "on_error": "Qual a **cidade**, por favor?"
            },
            "q9": {
                "id": "endereco_estado",
                "question": "Estado (UF – 2 letras), ex.: SP, RJ, MG:",
                "validation": "UF brasileiro válido",
                "on_error": "Me diga a **UF** com 2 letras, ex.: PR, BA, RS."
            },
            "q10": {
                "id": "endereco_cep",
                "question": "CEP (somente números), por favor.",
                "validation": "8 dígitos",
                "on_error": "Consegue enviar o **CEP** com 8 números? Ex.: 01311000"
            },
            "q11": {
                "id": "email",
                "question": "Perfeito! Seu **e-mail principal**? Vou enviar a simulação e depois o contrato por lá.",
                "validation": "padrão e-mail válido",
                "on_error": "Acho que esse e-mail não passou na validação. Pode revisar? Ex.: nome@dominio.com"
            },
            "q12": {
                "id": "nome_mae",
                "question": "Qual o **nome completo da sua mãe**? É uma confirmação padrão de cadastro.",
                "validation": "mín. 2 palavras",
                "on_error": "Preciso do **nome completo da mãe**, por favor."
            },
            "q13": {
                "id": "renda",
                "question": "Pra adequar as opções, qual sua **renda mensal** aproximada? Pode enviar apenas números. Ex.: 3500",
                "validation": "apenas números",
                "on_error": "Me manda apenas números, por favor? Ex.: 3500"
            },
            "q14": {
                "id": "profissao",
                "question": "E sua **profissão/ocupação** atual?",
                "validation": "mín. 2 caracteres",
                "on_error": "Qual sua **profissão/ocupação** atual?"
            },
            "q15": {
                "id": "whatsapp",
                "question": "Confirma pra mim seu **WhatsApp** com DDD? É esse mesmo que estamos falando ou é outro? É por onde o especialista irá te chamar caso necessário.",
                "validation": "apenas números (10 a 11 dígitos)",
                "on_error": "Pode me enviar seu **WhatsApp** só com números (DDD + número)? Ex.: 11987654321"
            },
            "q16": {
                "id": "consentimento",
                "question": "Tudo certo! Você **autoriza** o uso desses dados apenas para sua simulação, contato e emissão do contrato pela Na Rede Consórcios?",
                "options": ["Sim", "Não"],
                "on_error": "Posso registrar seu **OK** para uso dos dados apenas neste atendimento?"
            },
            "q17": {
                "id": "confirmacao_final",
                "question": "template_confirmacao",  # Will be formatted with collected data
                "options": ["Sim", "Corrigir"],
                "on_error": "Sem problemas! Me diga exatamente o que deseja **corrigir** (ex.: CPF, e-mail, endereço…)."
            },
            "q18": {
                "id": "proximo_passo",
                "question": "template_finalizacao",  # Will be formatted with contact info
                "terminal": True
            }
        }

    def _run(self, current_step: str, user_response: str, lead_data: Optional[Dict] = None) -> str:
        """
        Process the lead qualification step

        Args:
            current_step: Current question step (q1-q18)
            user_response: User's response
            lead_data: Previously collected data

        Returns:
            Next question or validation result
        """
        if lead_data is None:
            lead_data = {}

        try:
            # ✅ ROBUSTA: Normalize inputs to handle CrewAI variations
            normalized_current_step = self._normalize_input(current_step)
            normalized_user_response = self._normalize_input(user_response)
            normalized_lead_data = lead_data if isinstance(lead_data, dict) else {}

            print(f"📋 LEAD QUALIFICATION TOOL CALLED!")
            print(f"📋 Current Step: {normalized_current_step}")
            print(f"📋 User Response: {normalized_user_response}")
            print(f"📋 Lead Data: {normalized_lead_data}")
            logger.info(f"📋 QUALIFICATION: Processing lead qualification step: {normalized_current_step} with response: {normalized_user_response}")

            # Handle start of qualification
            if normalized_current_step == "start":
                print(f"📋 Starting qualification with q1")
                return self._get_question("q1")

            # Validate current response and proceed
            if normalized_current_step in self.questions:
                validation_result = self._validate_response(normalized_current_step, normalized_user_response, normalized_lead_data)

                if validation_result["valid"]:
                    # Store the validated data
                    field_id = self.questions[normalized_current_step]["id"]
                    normalized_lead_data[field_id] = validation_result["value"]

                    # Get next question
                    next_step = self._get_next_step(normalized_current_step)
                    if next_step:
                        return self._get_question(next_step, lead_data)
                    else:
                        return "🎉 Qualificação concluída!"

                else:
                    # Return error message
                    return self.questions[current_step]["on_error"]

            return "Etapa não reconhecida. Vamos começar do início?"

        except Exception as e:
            return f"Erro no processo de qualificação: {str(e)}"

    def _validate_response(self, step: str, response: str, lead_data: Dict) -> Dict:
        """Validate user response according to step requirements"""
        question = self.questions[step]
        response = response.strip()

        field_id = question["id"]
        validation = question.get("validation", "")

        # Handle options-based questions
        if "options" in question:
            if response in question["options"]:
                # Map option to value if mapping exists
                if "map" in question:
                    return {"valid": True, "value": question["map"][response]}
                return {"valid": True, "value": response}
            return {"valid": False}

        # Validation rules
        if field_id == "nome" or field_id == "nome_mae":
            if len(response.split()) >= 2:
                return {"valid": True, "value": response}

        elif field_id == "cpf":
            # Remove non-digits and validate CPF
            cpf = re.sub(r'\D', '', response)
            if len(cpf) == 11 and self._validate_cpf(cpf):
                return {"valid": True, "value": cpf}

        elif field_id == "naturalidade":
            # Check for city/UF format
            if "/" in response and len(response.split("/")) == 2:
                city, uf = response.split("/")
                if len(uf.strip()) == 2:
                    return {"valid": True, "value": response}

        elif field_id in ["endereco_rua", "endereco_bairro", "endereco_cidade"]:
            if len(response) >= 2:
                return {"valid": True, "value": response}

        elif field_id == "endereco_numero":
            if response.upper() == "S/N" or response.isdigit():
                return {"valid": True, "value": response}

        elif field_id == "endereco_estado":
            # List of valid Brazilian state codes
            valid_ufs = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
                        "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
                        "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
            if response.upper() in valid_ufs:
                return {"valid": True, "value": response.upper()}

        elif field_id == "endereco_cep":
            cep = re.sub(r'\D', '', response)
            if len(cep) == 8:
                return {"valid": True, "value": cep}

        elif field_id == "email":
            if "@" in response and "." in response:
                return {"valid": True, "value": response}

        elif field_id == "renda":
            # Extract numbers only
            renda = re.sub(r'\D', '', response)
            if renda:
                return {"valid": True, "value": renda}

        elif field_id == "profissao":
            if len(response) >= 2:
                return {"valid": True, "value": response}

        elif field_id == "whatsapp":
            phone = re.sub(r'\D', '', response)
            if 10 <= len(phone) <= 11:
                return {"valid": True, "value": phone}

        return {"valid": False}

    def _validate_cpf(self, cpf: str) -> bool:
        """Validate Brazilian CPF number"""
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False

        # Calculate first digit
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = 11 - (sum1 % 11)
        if digit1 >= 10:
            digit1 = 0

        # Calculate second digit
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = 11 - (sum2 % 11)
        if digit2 >= 10:
            digit2 = 0

        return cpf[9:11] == f"{digit1}{digit2}"

    def _get_question(self, step: str, lead_data: Optional[Dict] = None) -> str:
        """Get the question for a specific step"""
        if step not in self.questions:
            return "Etapa não encontrada."

        question = self.questions[step]

        # Handle template questions
        if question["question"] == "template_confirmacao":
            return self._format_confirmation_question(lead_data or {})
        elif question["question"] == "template_finalizacao":
            return self._format_finalization_message(lead_data or {})

        return question["question"]

    def _format_confirmation_question(self, lead_data: Dict) -> str:
        """Format the confirmation question with collected data"""
        endereco = f"{lead_data.get('endereco_rua', '')}, {lead_data.get('endereco_numero', '')} - {lead_data.get('endereco_bairro', '')}, {lead_data.get('endereco_cidade', '')}/{lead_data.get('endereco_estado', '')} - CEP: {lead_data.get('endereco_cep', '')}"

        cpf_mascarado = self._mask_cpf(lead_data.get('cpf', ''))
        whatsapp_formatado = self._format_phone(lead_data.get('whatsapp', ''))

        return f"""Ótimo! Vamos conferir tudo antes de seguir:
            • WhatsApp: {whatsapp_formatado}
            • Nome: {lead_data.get('nome', '')}
            • CPF: {cpf_mascarado}
            • Estado civil: {lead_data.get('estado_civil', '')}
            • Naturalidade: {lead_data.get('naturalidade', '')}
            • Endereço: {endereco}
            • E-mail: {lead_data.get('email', '')}
            • Nome da mãe: {lead_data.get('nome_mae', '')}
            • Renda: R$ {lead_data.get('renda', '')}
            • Profissão: {lead_data.get('profissao', '')}

            Está tudo **correto**?"""

    def _format_finalization_message(self, lead_data: Dict) -> str:
        """Format the finalization message"""
        whatsapp = self._format_phone(lead_data.get('whatsapp', ''))
        email = lead_data.get('email', '')

        return f"""Ótimo! Nosso especialista vai te contatar pelo **WhatsApp {whatsapp}** e enviar o **contrato no e-mail {email}**.

🎉 Parabéns pela conquista — ótima escolha!

✅ Seu cadastro foi registrado com sucesso
📞 Aguarde o contato em breve
📧 Fique de olho no seu e-mail

Obrigada por escolher a Na Rede Consórcios! 😊"""

    def _mask_cpf(self, cpf: str) -> str:
        """Mask CPF for display"""
        if len(cpf) == 11:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return cpf

    def _format_phone(self, phone: str) -> str:
        """Format phone number for display"""
        if len(phone) == 11:
            return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
        elif len(phone) == 10:
            return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
        return phone

    def _get_next_step(self, current_step: str) -> Optional[str]:
        """Get the next step in the qualification flow"""
        step_order = [f"q{i}" for i in range(1, 19)]

        try:
            current_index = step_order.index(current_step)
            if current_index < len(step_order) - 1:
                return step_order[current_index + 1]
        except ValueError:
            pass

        return None

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
                elif "current_step" in input_value:
                    return str(input_value["current_step"]).strip()
                elif "user_response" in input_value:
                    return str(input_value["user_response"]).strip()
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


# Instance for use in CrewAI
lead_qualification_tool = LeadQualificationTool()
