import sys
sys.path.insert(0, r"C:\Users\Fernando\Projects\AUTQS")

from src.agent.chat_agent import AutqsChatAgent

agent = AutqsChatAgent()
agent.edificio_ativo = "Flexinc - [055] Jardim Europa CA"

prompt = "Utilize como referncia para as cotas o 0,0 no ponto 17051.5856 , -4041.0557"
print(f"Enviando prompt: '{prompt}'...")
resp = agent.responder(prompt)

print("Tipo de resposta:", resp.get("tipo"))
print("\n--- Texto de resposta ---")
# Safely print text in utf-8
sys.stdout.reconfigure(encoding="utf-8")
print(resp.get("texto"))
