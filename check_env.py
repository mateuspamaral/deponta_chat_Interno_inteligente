"""Verifica se as credenciais estão preenchidas no .env"""
from dotenv import load_dotenv
import os

load_dotenv()

vars_check = {
    "BLING_CLIENT_ID": os.getenv("BLING_CLIENT_ID", ""),
    "BLING_CLIENT_SECRET": os.getenv("BLING_CLIENT_SECRET", ""),
    "BLING_REFRESH_TOKEN": os.getenv("BLING_REFRESH_TOKEN", ""),
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
}

all_ok = True
for name, val in vars_check.items():
    status = "OK" if val.strip() else "VAZIO"
    if status == "VAZIO":
        all_ok = False
    print(f"  {name}: {status}")

if all_ok:
    print("\nTodas as credenciais preenchidas. Pronto para testar!")
else:
    print("\nALERTA: Preencha as credenciais vazias no .env antes de rodar.")
