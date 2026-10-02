import os
import json
import requests
from typing import Dict, Any, List, Optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.agent.orchestrator import SYSTEM_PROMPT_AUTQS

class GeminiClient:
    """
    Cliente direto para o Google Gemini API (camada gratuita do Google AI Studio).
    Usa chamadas REST com 'requests' sem necessidade de SDKs pesados adicionais.
    Modelo padrão: gemini-3.8-flash (alta velocidade, gratuito, 15 RPM / 1.500 RPD).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        # Modelos gratuitos ordenados por alta disponibilidade e velocidade
        self.modelos_candidatos = [
            "gemini-3.6-flash",
            "gemini-3.1-flash-lite",
            "gemini-3.8-flash",
            "gemini-flash-latest",
        ]
        self.modelo_ativo = "gemini-3.6-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def esta_configurado(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    def gerar_resposta(
        self,
        mensagens: List[Dict[str, str]],
        contexto_estrutural: str = "",
        ferramentas: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Envia o histórico de conversa e o contexto estrutural do TQS para o Gemini.
        """
        if not self.esta_configurado():
            return {
                "sucesso": False,
                "erro": "Chave da API do Gemini não configurada. Obtenha uma chave gratuita em aistudio.google.com",
            }

        prompt_sistema = SYSTEM_PROMPT_AUTQS
        if contexto_estrutural:
            prompt_sistema += f"\n\nCONTEXTO DO PROJETO ATUAL DO TQS:\n{contexto_estrutural}"

        # Monta o payload no padrão Gemini REST
        contents = []
        for m in mensagens:
            role = "user" if m["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })

        payload = {
            "systemInstruction": {
                "parts": [{"text": prompt_sistema}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
            }
        }

        headers = {"Content-Type": "application/json"}
        ultimo_erro = "Erro desconhecido"

        for mod in self.modelos_candidatos:
            url = f"{self.base_url}/{mod}:generateContent?key={self.api_key.strip()}"
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    candidatos = data.get("candidates", [])
                    if candidatos:
                        self.modelo_ativo = mod
                        texto = candidatos[0]["content"]["parts"][0]["text"]
                        return {"sucesso": True, "texto": texto, "modelo": mod}
                    return {"sucesso": False, "erro": "Resposta vazia do modelo Gemini."}
                elif resp.status_code in [404, 429, 500, 502, 503, 504]:
                    ultimo_erro = f"Modelo {mod} retornou HTTP {resp.status_code}."
                    continue
                else:
                    return {
                        "sucesso": False,
                        "erro": f"Erro na API do Gemini (HTTP {resp.status_code}): {resp.text}",
                    }
            except Exception as e:
                ultimo_erro = str(e)
                continue

        return {"sucesso": False, "erro": f"Falha na comunicação com o Gemini: {ultimo_erro}"}
