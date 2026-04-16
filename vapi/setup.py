"""Create the Boston 311 Vapi voice agent: upload KB files, create tools, create assistant."""

import json
import os
import requests

VAPI_BASE = "https://api.vapi.ai"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
STATIC_DIR = os.path.join(PROJECT_DIR, "knowledge-base", "static")

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
    """Upload knowledge base markdown files to Vapi."""
    file_ids = []
    for fname in sorted(os.listdir(STATIC_DIR)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(STATIC_DIR, fname)
        print(f"  Uploading {fname}...")
        r = requests.post(
            f"{VAPI_BASE}/file",
            headers={"Authorization": f"Bearer {VAPI_KEY}"},
            files={"file": (fname, open(fpath, "rb"), "text/markdown")},
        )
        if not r.ok:
            print(f"  ERROR uploading {fname}: {r.status_code} {r.text[:300]}")
            continue
        fid = r.json().get("id")
        print(f"  -> {fid}")
        file_ids.append(fid)
    return file_ids


def read_tool_code(filename):
    with open(os.path.join(SCRIPT_DIR, "tools", filename)) as f:
        return f.read()


def create_tools():
    """Create the 3 code tools in Vapi."""
    tools = {}

    # 1. list_services
    print("  Creating list_services tool...")
    t = api(
        "POST",
        "/tool",
        json={
            "type": "code",
            "function": {
                "name": "list_services",
                "description": "List all available Boston 311 service request types the caller can report. Use this when the caller's issue doesn't clearly match a known service type.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            "code": read_tool_code("list_services.ts"),
            "messages": [
                {
                    "type": "request-start",
                    "content": "Let me check what services are available.",
                },
                {
                    "type": "request-failed",
                    "content": "I'm having trouble reaching the service list right now.",
                },
            ],
        },
    )
    tools["list_services"] = t["id"]
    print(f"  -> {t['id']}")

    # 2. create_ticket
    print("  Creating create_ticket tool...")
    t = api(
        "POST",
        "/tool",
        json={
            "type": "code",
            "function": {
                "name": "create_ticket",
                "description": "Submit a new 311 service request (ticket) to the City of Boston. Call this after collecting the service type, address, and description from the caller.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_code": {
                            "type": "string",
                            "description": "The Open311 service_code for the issue type.",
                        },
                        "address": {
                            "type": "string",
                            "description": "Street address or intersection where the issue is located.",
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the issue as reported by the caller.",
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
                            "description": "Caller's email for follow-up (optional).",
                        },
                        "phone": {
                            "type": "string",
                            "description": "Caller's phone number (optional).",
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
                    "content": "I'm submitting your request now. One moment please.",
                },
                {
                    "type": "request-complete",
                    "content": "Your request has been submitted.",
                },
                {
                    "type": "request-failed",
                    "content": "I wasn't able to submit the request. You can also report this by calling 3-1-1 directly or using the BOS 311 app.",
                },
            ],
        },
    )
    tools["create_ticket"] = t["id"]
    print(f"  -> {t['id']}")

    # 3. check_ticket_status
    print("  Creating check_ticket_status tool...")
    t = api(
        "POST",
        "/tool",
        json={
            "type": "code",
            "function": {
                "name": "check_ticket_status",
                "description": "Look up the current status of an existing Boston 311 service request by its ID number.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_request_id": {
                            "type": "string",
                            "description": "The service request ID number to look up.",
                        },
                    },
                    "required": ["service_request_id"],
                },
            },
            "code": read_tool_code("check_status.ts"),
            "messages": [
                {"type": "request-start", "content": "Let me look that up for you."},
                {
                    "type": "request-failed",
                    "content": "I couldn't find that request. Please double-check the number.",
                },
            ],
        },
    )
    tools["check_ticket_status"] = t["id"]
    print(f"  -> {t['id']}")

    return tools


def create_assistant(tool_ids, file_ids):
    """Create the Vapi assistant with tools and knowledge base."""
    with open(os.path.join(SCRIPT_DIR, "system_prompt.txt")) as f:
        system_prompt = f.read()

    print("  Creating assistant...")
    assistant = api(
        "POST",
        "/assistant",
        json={
            "name": "Boston 311 Agent",
            "firstMessage": "Hello, you've reached Boston 3-1-1. I can help you report non-emergency city issues or check on an existing request. How can I assist you today?",
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "messages": [{"role": "system", "content": system_prompt}],
                "toolIds": list(tool_ids.values()),
            },
            "silenceTimeoutSeconds": 30,
            "maxDurationSeconds": 600,
            "endCallMessage": "Thank you for calling Boston 3-1-1. Have a great day!",
            "endCallPhrases": ["goodbye", "bye", "that's all", "nothing else"],
        },
    )

    assistant_id = assistant["id"]
    print(f"  -> Assistant ID: {assistant_id}")

    # Attach knowledge base files if we have them
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
    print("=== Boston 311 Vapi Agent Setup ===\n")

    print("[1/3] Uploading knowledge base files...")
    file_ids = upload_files()
    print(f"  Uploaded {len(file_ids)} files\n")

    print("[2/3] Creating tools...")
    tool_ids = create_tools()
    print(f"  Created {len(tool_ids)} tools\n")

    print("[3/3] Creating assistant...")
    assistant_id = create_assistant(tool_ids, file_ids)

    print(f"\n=== DONE ===")
    print(f"Assistant ID: {assistant_id}")
    print(f"Dashboard:    https://dashboard.vapi.ai/assistants/{assistant_id}")
    print(f"\nYou can test it via:")
    print(f"  - Vapi Dashboard: click 'Talk' on the assistant page")
    print(f"  - Vapi Web SDK:   use assistant ID '{assistant_id}'")
    print(f"  - Vapi phone:     assign a phone number in the dashboard")

    # Save assistant ID to config
    config["assistant_id"] = assistant_id
    config["tool_ids"] = tool_ids
    config["file_ids"] = file_ids
    with open(os.path.join(SCRIPT_DIR, "config.json"), "w") as f:
        json.dump(config, f, indent=2)
    print(f"\nConfig updated with assistant_id and tool_ids.")


if __name__ == "__main__":
    main()
