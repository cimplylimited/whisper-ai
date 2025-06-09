"""
check_env.py  ‒  quick diagnostics for .env loading

• Shows which .env file is being read
• Prints every line in that file (raw)
• Prints environment-variable values exactly as Python sees them
  (no stripping / no extra quoting)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ------------------------------------------------------------------
# 1) Locate .env   (you can override with ENV_PATH)
# ------------------------------------------------------------------
env_path = os.getenv("DOCGEN_ENV_PATH") or ".env"
env_path = Path(env_path).expanduser().resolve()

print(f"\n>>> .env path resolved to:  {env_path}\n")

if not env_path.exists():
    print("File does NOT exist.  Abort.")
    raise SystemExit(1)

# ------------------------------------------------------------------
# 2) Show raw file contents
# ------------------------------------------------------------------
print("-----  RAW .env CONTENTS  --------")
with env_path.open() as fh:
    for i, line in enumerate(fh, 1):
        print(f"{i:>3}: {line.rstrip()}")
print("-----------------------------------\n")

# ------------------------------------------------------------------
# 3) Load into environment (overwriting duplicates)
# ------------------------------------------------------------------
load_dotenv(dotenv_path=env_path, override=True)

# List which variables we care about:
keys_of_interest = [
    "OUTPUT_FOLDER_ID",
    "PROCESSED_FOLDER_ID",
    "RECORDING_FOLDER_IDS",
    "SERVICE_ACCOUNT_FILE",
    "OPENAI_MODEL_NAME",
]

print("-----  os.getenv AFTER load_dotenv  --------")
for k in keys_of_interest:
    print(f"{k:<20}= {os.getenv(k)}")
print("--------------------------------------------")

# Show cwd / __file__ so you know where the script is executed from
print("\nCurrent working directory :", Path.cwd())
print("This script location      :", Path(__file__).resolve())