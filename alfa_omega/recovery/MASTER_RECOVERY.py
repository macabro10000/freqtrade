# ============================================================
# ALFA OMEGA TRADING
# MASTER RECOVERY
# ============================================================
#
# Este archivo es el núcleo de recuperación del proyecto.
#
# OBJETIVO:
# Reconstruir el entorno de Colab y detectar el último punto
# persistente del sistema sin repetir trabajos terminados.
#
# ============================================================

import json
import os
import subprocess
import sys
from datetime import UTC, datetime

# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------

PROJECT = "ALFA OMEGA TRADING"

GITHUB_REPO = "macabro10000/freqtrade"
GITHUB_BRANCH = "develop"

HF_DATASET = "Macabro10000/trading-data"

MONGODB_HOST = "alfaomega.yr4r1no.mongodb.net"
MONGODB_DATABASE = "trading_system"
MONGODB_COLLECTION = "system_status"

RENDER_HEALTH_URL = (
    "https://alfa-omega-trading.onrender.com/api/health"
)

LOCAL_ROOT = "/content/alfa_omega_data"
RECOVERY_ROOT = "/content/alfa_omega_recovery"

MARKETS = [
    "BTCUSD",
    "XAUUSD",
]

TIMEFRAMES = [
    "1m",
    "5m",
    "15m",
    "1h",
    "4h",
    "1d",
    "1w",
]

# ------------------------------------------------------------
# TIEMPO
# ------------------------------------------------------------

def utc_now():
    return datetime.now(UTC).isoformat()

# ------------------------------------------------------------
# DIRECTORIOS LOCALES
# ------------------------------------------------------------

def create_local_structure():

    directories = [
        LOCAL_ROOT,
        RECOVERY_ROOT,
    ]

    for market in MARKETS:

        market_root = os.path.join(
            LOCAL_ROOT,
            market
        )

        directories.append(market_root)

        for timeframe in TIMEFRAMES:

            directories.append(
                os.path.join(
                    market_root,
                    timeframe
                )
            )

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# ------------------------------------------------------------
# INSTALAR DEPENDENCIAS
# ------------------------------------------------------------

def install_dependencies():

    packages = [
        "PyGithub",
        "pymongo",
        "huggingface_hub",
        "requests",
        "pandas",
        "numpy",
        "pyarrow",
    ]

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
        ] + packages
    )

# ------------------------------------------------------------
# LEER SECRETS DE COLAB
# ------------------------------------------------------------

def load_colab_secrets():

    from google.colab import userdata

    secrets = {}

    names = [
        "GITHUB_TOKEN",
        "HF_TOKEN",
        "MONGODB_USER",
        "MONGODB_PASSWORD",
    ]

    for name in names:

        try:
            value = userdata.get(name)
        except Exception:
            value = None

        secrets[name] = value

    return secrets

# ------------------------------------------------------------
# GITHUB
# ------------------------------------------------------------

def check_github(token):

    from github import Github, Auth

    auth = Auth.Token(token)

    gh = Github(auth=auth)

    user = gh.get_user()
    repo = gh.get_repo(GITHUB_REPO)

    return {
        "status": "CONNECTED",
        "user": user.login,
        "repository": repo.full_name,
        "branch": GITHUB_BRANCH,
    }

# ------------------------------------------------------------
# HUGGING FACE
# ------------------------------------------------------------

def check_huggingface(token):

    from huggingface_hub import HfApi

    api = HfApi(token=token)

    files = api.list_repo_files(
        repo_id=HF_DATASET,
        repo_type="dataset",
    )

    return {
        "status": "CONNECTED",
        "dataset": HF_DATASET,
        "files": len(files),
    }

# ------------------------------------------------------------
# MONGODB
# ------------------------------------------------------------

def check_mongodb(user, password):

    from pymongo import MongoClient

    uri = (
        "mongodb+srv://"
        + user
        + ":"
        + password
        + "@"
        + MONGODB_HOST
        + "/"
        + MONGODB_DATABASE
        + "?retryWrites=true&w=majority&appName=Alfaomega"
    )

    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=10000,
    )

    client.admin.command("ping")

    collection = client[
        MONGODB_DATABASE
    ][
        MONGODB_COLLECTION
    ]

    latest = collection.find_one(
        {
            "project": PROJECT,
        },
        sort=[
            ("created_at", -1)
        ],
    )

    return {
        "status": "CONNECTED",
        "database": MONGODB_DATABASE,
        "collection": MONGODB_COLLECTION,
        "latest_checkpoint": latest,
        "client": client,
    }

# ------------------------------------------------------------
# RENDER
# ------------------------------------------------------------

def check_render():

    import requests

    try:

        response = requests.get(
            RENDER_HEALTH_URL,
            timeout=15,
        )

        return {
            "status": "CONNECTED"
                if response.ok
                else "ERROR",
            "http_status": response.status_code,
            "response": response.text[:1000],
        }

    except Exception as error:

        return {
            "status": "ERROR",
            "error": str(error),
        }

# ------------------------------------------------------------
# ESCANEAR DATOS LOCALES
# ------------------------------------------------------------

def scan_local_data():

    result = {
        "root_exists": os.path.exists(LOCAL_ROOT),
        "files": [],
    }

    if not os.path.exists(LOCAL_ROOT):
        return result

    for root, _dirs, files in os.walk(LOCAL_ROOT):

        for filename in files:

            path = os.path.join(
                root,
                filename
            )

            try:
                size = os.path.getsize(path)
            except Exception:
                size = None

            result["files"].append(
                {
                    "path": path,
                    "size": size,
                }
            )

    return result

# ------------------------------------------------------------
# RECUPERACIÓN
# ------------------------------------------------------------

def run_recovery():

    print()
    print("=" * 60)
    print(PROJECT)
    print("MASTER RECOVERY")
    print("=" * 60)
    print()

    print("1️⃣ Instalando dependencias...")
    install_dependencies()
    print("🟢 Dependencias listas")
    print()

    print("2️⃣ Leyendo Secrets...")
    secrets = load_colab_secrets()

    required = [
        "GITHUB_TOKEN",
        "HF_TOKEN",
        "MONGODB_USER",
        "MONGODB_PASSWORD",
    ]

    for name in required:

        if not secrets.get(name):

            raise RuntimeError(
                "Falta el Secret de Colab: " + name
            )

    print("🟢 Secrets disponibles")
    print()

    print("3️⃣ Comprobando GitHub...")

    github = check_github(
        secrets["GITHUB_TOKEN"]
    )

    print("🟢 GitHub:", github["repository"])
    print()

    print("4️⃣ Comprobando Hugging Face...")

    hf = check_huggingface(
        secrets["HF_TOKEN"]
    )

    print(
        "🟢 Hugging Face:",
        hf["files"],
        "archivos"
    )

    print()

    print("5️⃣ Comprobando MongoDB...")

    mongo = check_mongodb(
        secrets["MONGODB_USER"],
        secrets["MONGODB_PASSWORD"],
    )

    print(
        "🟢 MongoDB:",
        mongo["database"]
    )

    print()

    print("6️⃣ Comprobando Render...")

    render = check_render()

    print(
        "🟢 Render:",
        render["status"]
    )

    print()

    print("7️⃣ Reconstruyendo estructura local...")

    create_local_structure()

    print("🟢 Estructura local lista")
    print()

    print("8️⃣ Buscando datos locales...")

    local = scan_local_data()

    print(
        "📂 Archivos encontrados:",
        len(local["files"])
    )

    print()

    # --------------------------------------------------------
    # CREAR ESTADO DE RECUPERACIÓN
    # --------------------------------------------------------

    state = {

        "project": PROJECT,

        "recovery_time": utc_now(),

        "github": {
            "status": github["status"],
            "repository": github["repository"],
            "branch": github["branch"],
        },

        "huggingface": {
            "status": hf["status"],
            "dataset": hf["dataset"],
            "files": hf["files"],
        },

        "mongodb": {
            "status": mongo["status"],
            "database": mongo["database"],
            "collection": mongo["collection"],
        },

        "render": {
            "status": render["status"],
            "http_status": render.get(
                "http_status"
            ),
        },

        "local_data": {
            "files": len(
                local["files"]
            ),
        },

        "markets": MARKETS,

        "timeframes": TIMEFRAMES,

    }

    os.makedirs(
        RECOVERY_ROOT,
        exist_ok=True
    )

    state_path = os.path.join(
        RECOVERY_ROOT,
        "runtime_state.json"
    )

    with open(
        state_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            state,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # GUARDAR CHECKPOINT
    # --------------------------------------------------------

    collection = mongo["client"][
        MONGODB_DATABASE
    ][
        MONGODB_COLLECTION
    ]

    collection.insert_one(
        {
            "project": PROJECT,
            "type": "master_recovery",
            "status": "COMPLETED",
            "created_at": utc_now(),
            "markets": MARKETS,
            "timeframes": TIMEFRAMES,
            "runtime_state": state,
        }
    )

    print("=" * 60)
    print("🎯 RECUPERACIÓN COMPLETADA")
    print("=" * 60)
    print()
    print("GitHub       :", github["status"])
    print("Hugging Face :", hf["status"])
    print("MongoDB      :", mongo["status"])
    print("Render       :", render["status"])
    print()
    print("📌 Estado guardado en:")
    print(state_path)
    print()
    print("⚠️ Este módulo todavía NO descarga datos.")
    print("⚠️ Su función es reconstruir y recuperar el entorno.")
    print()

    mongo["client"].close()

# ------------------------------------------------------------
# EJECUCIÓN
# ------------------------------------------------------------

if __name__ == "__main__":
    run_recovery()
