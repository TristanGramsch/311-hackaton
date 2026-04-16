"""Create the bilingual (EN/ES) Boston 311 Vapi voice agent."""

import json
import os
import requests

VAPI_BASE = "https://api.vapi.ai"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
STATIC_EN = os.path.join(PROJECT_DIR, "knowledge-base", "static")
STATIC_ES = os.path.join(PROJECT_DIR, "knowledge-base", "static-es")

with open(os.path.join(SCRIPT_DIR, "config.json")) as f:
    config = json.load(f)

VAPI_KEY = config["vapi_api_key"]
HEADERS = {"Authorization": f"Bearer {VAPI_KEY}", "Content-Type": "application/json"}


def api(method, path, **kwargs):
    r = requests.request(method, f"{VAPI_BASE}{path}", headers=HEADERS, **kwargs)
    if not r.ok:
        print(f"ERROR {r.status_code} {path}: {r.text[:500]}")
        r.raise_for_status()
    return r.json()


def upload_files():
    """Upload English and Spanish KB files."""
    file_ids = []
    for label, directory in [("EN", STATIC_EN), ("ES", STATIC_ES)]:
        for fname in sorted(os.listdir(directory)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(directory, fname)
            upload_name = f"{label}_{fname}"
            print(f"  Uploading {upload_name}...")
            r = requests.post(
                f"{VAPI_BASE}/file",
                headers={"Authorization": f"Bearer {VAPI_KEY}"},
                files={"file": (upload_name, open(fpath, "rb"), "text/markdown")},
            )
            if not r.ok:
                print(f"  ERROR: {r.status_code} {r.text[:200]}")
                continue
            fid = r.json().get("id")
            print(f"  -> {fid}")
            file_ids.append(fid)
    return file_ids


def bilingual_msg(en, es):
    """Create a Vapi contents array with EN and ES variants."""
    return [
        {"type": "text", "text": en, "language": "en"},
        {"type": "text", "text": es, "language": "es"},
    ]


def read_tool_code(filename):
    with open(os.path.join(SCRIPT_DIR, "tools", filename)) as f:
        return f.read()


def create_tools():
    """Create 3 bilingual code tools."""
    tools = {}

    print("  Creating list_services tool...")
    t = api(
        "POST",
        "/tool",
        json={
            "type": "code",
            "function": {
                "name": "list_services",
                "description": "List all available Boston 311 service request types.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            "code": read_tool_code("list_services.ts"),
            "messages": [
                {
                    "type": "request-start",
                    "contents": bilingual_msg(
                        "Let me check what services are available.",
                        "Permítame verificar qué servicios están disponibles.",
                    ),
                },
                {
                    "type": "request-failed",
                    "contents": bilingual_msg(
                        "I'm having trouble reaching the service list right now.",
                        "Estoy teniendo problemas para acceder a la lista de servicios en este momento.",
                    ),
                },
            ],
        },
    )
    tools["list_services"] = t["id"]
    print(f"  -> {t['id']}")

    print("  Creating create_ticket tool...")
    t = api(
        "POST",
        "/tool",
        json={
            "type": "code",
            "function": {
                "name": "create_ticket",
                "description": "Submit a new 311 service request to the City of Boston.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_code": {
                            "type": "string",
                            "description": "The Open311 service_code.",
                        },
                        "address": {
                            "type": "string",
                            "description": "Street address or intersection.",
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the issue.",
                        },
                        "first_name": {
                            "type": "string",
                            "description": "Caller's first name (optional).",
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Caller's last name (optional).",
                        },
                        "email": {
                            "type": "string",
                            "description": "Caller's email (optional).",
                        },
                        "phone": {
                            "type": "string",
                            "description": "Caller's phone (optional).",
                        },
                    },
                    "required": ["service_code", "address", "description"],
                },
            },
            "code": read_tool_code("create_ticket.ts"),
            "environmentVariables": [
                {"name": "OPEN311_API_KEY", "value": config.get("open311_api_key", "")},
            ],
            "messages": [
                {
                    "type": "request-start",
                    "contents": bilingual_msg(
                        "I'm submitting your request now. One moment please.",
                        "Estoy enviando su solicitud ahora. Un momento por favor.",
                    ),
                },
                {
                    "type": "request-complete",
                    "contents": bilingual_msg(
                        "Your request has been submitted.",
                        "Su solicitud ha sido enviada.",
                    ),
                },
                {
                    "type": "request-failed",
                    "contents": bilingual_msg(
                        "I wasn't able to submit the request. You can also call 3-1-1 directly or use the BOS 311 app.",
                        "No pude enviar la solicitud. También puede llamar al 3-1-1 directamente o usar la app BOS 311.",
                    ),
                },
            ],
        },
    )
    tools["create_ticket"] = t["id"]
    print(f"  -> {t['id']}")

    print("  Creating check_ticket_status tool...")
    t = api(
        "POST",
        "/tool",
        json={
            "type": "code",
            "function": {
                "name": "check_ticket_status",
                "description": "Look up the status of an existing Boston 311 service request.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_request_id": {
                            "type": "string",
                            "description": "The service request ID.",
                        },
                    },
                    "required": ["service_request_id"],
                },
            },
            "code": read_tool_code("check_status.ts"),
            "messages": [
                {
                    "type": "request-start",
                    "contents": bilingual_msg(
                        "Let me look that up for you.",
                        "Permítame buscar eso para usted.",
                    ),
                },
                {
                    "type": "request-failed",
                    "contents": bilingual_msg(
                        "I couldn't find that request. Please double-check the number.",
                        "No pude encontrar esa solicitud. Por favor verifique el número.",
                    ),
                },
            ],
        },
    )
    tools["check_ticket_status"] = t["id"]
    print(f"  -> {t['id']}")

    return tools


def create_assistant(tool_ids, file_ids):
    """Create the bilingual Vapi assistant."""
    with open(os.path.join(SCRIPT_DIR, "system_prompt_bilingual.txt")) as f:
        system_prompt = f.read()

    print("  Creating assistant...")
    assistant = api(
        "POST",
        "/assistant",
        json={
            "name": "Boston 311 Agent (Bilingual EN/ES)",
            "firstMessage": "Hello, you've reached Boston 3-1-1. I can help in English or Spanish. How can I assist you today? / Hola, se ha comunicado con Boston 3-1-1. Puedo ayudarle en inglés o español. ¿En qué puedo ayudarle?",
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "messages": [{"role": "system", "content": system_prompt}],
                "toolIds": list(tool_ids.values()),
            },
            "transcriber": {
                "provider": "deepgram",
                "language": "en",
                "model": "nova-3",
            },
            "silenceTimeoutSeconds": 30,
            "maxDurationSeconds": 600,
            "endCallMessage": "Thank you for calling Boston 3-1-1. Have a great day! / Gracias por llamar a Boston 3-1-1. ¡Que tenga un buen día!",
            "endCallPhrases": [
                "goodbye",
                "bye",
                "that's all",
                "nothing else",
                "adiós",
                "eso es todo",
                "nada más",
                "gracias",
            ],
        },
    )

    assistant_id = assistant["id"]
    print(f"  -> Assistant ID: {assistant_id}")

    if file_ids:
        print("  Attaching knowledge base files...")
        try:
            api(
                "PATCH",
                f"/assistant/{assistant_id}",
                json={
                    "model": {
                        "provider": "openai",
                        "model": "gpt-4o",
                        "messages": [{"role": "system", "content": system_prompt}],
                        "toolIds": list(tool_ids.values()),
                        "knowledgeBase": {
                            "provider": "canonical",
                            "fileIds": file_ids,
                        },
                    },
                },
            )
            print("  -> Knowledge base attached")
        except Exception as e:
            print(f"  -> KB attachment failed (non-critical): {e}")

    return assistant_id


def main():
    print("=== Boston 311 Bilingual (EN/ES) Vapi Agent Setup ===\n")

    print("[1/3] Uploading knowledge base files (EN + ES)...")
    file_ids = upload_files()
    print(f"  Uploaded {len(file_ids)} files\n")

    print("[2/3] Creating bilingual tools...")
    tool_ids = create_tools()
    print(f"  Created {len(tool_ids)} tools\n")

    print("[3/3] Creating bilingual assistant...")
    assistant_id = create_assistant(tool_ids, file_ids)

    print(f"\n=== DONE ===")
    print(f"Assistant ID: {assistant_id}")
    print(f"Dashboard:    https://dashboard.vapi.ai/assistants/{assistant_id}")
    print(f"\nTest it via the Vapi Dashboard — try speaking in English or Spanish.")

    config["bilingual_assistant_id"] = assistant_id
    config["bilingual_tool_ids"] = tool_ids
    config["bilingual_file_ids"] = file_ids
    with open(os.path.join(SCRIPT_DIR, "config.json"), "w") as f:
        json.dump(config, f, indent=2)
    print(f"\nConfig updated with bilingual_assistant_id.")


if __name__ == "__main__":
    main()
