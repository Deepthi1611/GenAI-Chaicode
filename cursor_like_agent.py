# llm_project_creator.py
import os
import json
import time
import pathlib
import traceback
from dotenv import load_dotenv
from openai import OpenAI

# load .env if present
load_dotenv()


client = OpenAI(
    api_key=os.getenv('GOOGLE_API_KEY'),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


# base working directory where projects will be created
BASE_WORKDIR = os.getcwd()

# ------------------ Safety helpers ------------------
def safe_join_project(project_root: str, rel_path: str) -> str:
    """
    Ensure no absolute paths or '..' traversal.
    Returns absolute path inside project_root or raises ValueError.
    """
    if os.path.isabs(rel_path):
        raise ValueError("Absolute paths are not allowed.")
    if ".." in pathlib.Path(rel_path).parts:
        raise ValueError("Path traversal is not allowed.")
    full = os.path.abspath(os.path.join(project_root, rel_path))
    if not str(full).startswith(os.path.abspath(project_root) + os.sep) and str(full) != os.path.abspath(project_root):
        raise ValueError("Resulting path escapes project root.")
    return full

# ------------------ Tools (filesystem operations) ------------------
def create_folder_tool(project_root: str, tool_input):
    """
    tool_input: string (path) or {"path": "..."}
    Creates folder inside project_root.
    Prevents nested project folder duplication.
    """
    try:
        # Normalize input
        if isinstance(tool_input, str):
            payload = {"path": tool_input}
        elif isinstance(tool_input, dict):
            payload = tool_input
        else:
            return "ERROR: invalid input for create_folder"

        rel = payload.get("path", "").strip()
        if not rel:
            return "ERROR: 'path' required"

        # If model tries to recreate root folder, ignore silently
        if rel == project_root or rel.startswith(project_root):
            return f"Ignored duplicate project root creation: {rel}"

        # Build safe path
        full = safe_join_project(project_root, rel)

        os.makedirs(full, exist_ok=True)
        return f"Folder created: {rel}"

    except Exception as e:
        return f"ERROR create_folder: {e}"

def write_file_tool(project_root: str, tool_input):
    """
    tool_input: {"path": "...", "content": "..."}
    Safe file writing without escaped characters or commented-out code.
    """
    try:
        # Normalize input
        if isinstance(tool_input, str):
            try:
                payload = json.loads(tool_input)
            except Exception:
                return "ERROR: write_file expects a JSON string or dict."
        elif isinstance(tool_input, dict):
            payload = tool_input
        else:
            return "ERROR: invalid input type for write_file"

        rel = payload.get("path", "").strip()
        content = payload.get("content", "")

        if not rel:
            return "ERROR: 'path' is required for write_file"

        # Unescape escaped JSON content from LLM
        if isinstance(content, str):
            content = content.encode("utf-8").decode("unicode_escape")

        # Normalize newlines
        content = content.replace("\\n", "\n")

        # Remove accidental model-added comment prefixes
        if content.startswith("// ") or content.startswith("# "):
            # Only remove if the entire file gets commented accidentally
            lines = content.split("\n")
            if all(line.strip().startswith("//") or line.strip().startswith("#") for line in lines[:5]):
                lines = [line.lstrip("/# ").rstrip() for line in lines]
                content = "\n".join(lines)

        # Build safe path
        full_path = safe_join_project(project_root, rel)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Idempotent write:
        # Prevents rewriting identical content on retries
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    existing = f.read()
                if existing == content:
                    return f"File already up-to-date: {rel}"
            except:
                pass

        # Write file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"File written: {rel} ({len(content)} bytes)"

    except Exception as e:
        return f"ERROR write_file: {e}\n{traceback.format_exc()}"

# ------------------ LLM conversation helpers ------------------
SYSTEM_PROMPT = """
You are a file-creation coding assistant. The user gives you a project_name and a language/framework.
You MUST plan and then create the project by issuing ACTION JSON objects that call the provided tools.
You are allowed ONLY the following tools (use exactly their names):
- create_folder
- write_file

Protocol:
- Every assistant response MUST be a single JSON object (no extra text) matching this schema:
  {
    "step": "<start|plan|action|observe|result>",
    "function": "<create_folder | write_file | empty string>",
    "tool_input": "<string or JSON object>",
    "content": "<human-readable text>"
  }

- "plan" responses explain what you will do.
- "action" responses call ONE tool per response. Set "function" to the tool name and "tool_input" to the argument.
- After each action, wait for the tool observation, and then plan the next step or finish with "result".
- When creating files, create the project root folder first (project_name), then subfolders, then files.
- All paths must be relative to the project root folder. Never use absolute paths or "..".
- Use small, focused file-write actions: create each file separately with write_file.
- Use deterministic setting: keep responses concise and focused.

When asked to create a project, produce the full set of actions necessary to create a working boilerplate (folder + files). For JavaScript/Express, include server.js, src/app.js, routes, controllers, models, package.json. For FastAPI, include app/main.py, routers, models/schemas/services, requirements.txt, README.
Never call create_folder with the project root name. 
The root folder is already created by the agent. 
Only create folders INSIDE the project root.
Also add code in all created files and each folder should have atleast one file in it.
"""

MODEL_NAME = "gemini-2.5-flash"   # ADD THIS

def call_model_with_retry(messages):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            response_format={"type": "json_object"},
            messages=messages
        )
        return response
    except Exception as e:
        # Detect rate limit 429
        if "429" in str(e):
            print("Rate limit exceeded. Retrying in 5 seconds...")
            time.sleep(5)
            return call_model_with_retry(messages)

        print("Error:", e)
        raise e

# ------------------ Main interactive flow ------------------
def run_interactive():
    print("LLM Project Creator — local mode")
    project_name = input("Project name (single word, e.g., ecommerce): ").strip()
    if not project_name:
        print("Project name required.")
        return
    language = input("Language/framework (javascript | express | python | fastapi): ").strip().lower()
    if language not in ("javascript", "express", "js", "python", "fastapi", "py"):
        print("Unsupported language. Use 'javascript' or 'python' or 'fastapi' or 'express'.")
        return

    project_root = os.path.join(BASE_WORKDIR, project_name)
    if os.path.exists(project_root):
        confirmed = input(f"Folder {project_root} already exists — overwrite? (y/N): ").strip().lower()
        if confirmed != "y":
            print("Aborting.")
            return

    # start conversation
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps({"project_name": project_name, "language": language})}
    ]

    print("\nRequesting plan from LLM (this will instruct it to create folders & files)...\n")

    while True:
        # call model to get assistant JSON (plan or action)
        resp = call_model_with_retry(messages)
        # the client returns a JSON object in resp.choices[0].message.content
        try:
            assistant_json = resp.choices[0].message.content
            if isinstance(assistant_json, dict):
                parsed = assistant_json
            else:
                # JSON string
                parsed = json.loads(assistant_json)
        except Exception as e:
            print("ERROR parsing model JSON:", e)
            print("Raw assistant content:", resp.choices[0].message.content)
            return

        # append assistant message to history (as JSON string for traceability)
        messages.append({"role": "assistant", "content": json.dumps(parsed)})

        step = parsed.get("step")
        func = parsed.get("function", "")
        tool_input = parsed.get("tool_input", "")
        content = parsed.get("content", "")

        if step == "plan" or step == "start":
            print("PLAN:", content)
            # continue to next model call (model should emit an action next)
            continue

        elif step == "action":
            # execute exactly one tool
            print("ACTION ->", func, "| tool_input:", tool_input if len(str(tool_input)) < 500 else "(large payload)")

            # prepare tool execution
            try:
                # parse tool input into python object if it's a JSON string
                if isinstance(tool_input, str):
                    try:
                        tinput_obj = json.loads(tool_input)
                    except Exception:
                        tinput_obj = tool_input
                else:
                    tinput_obj = tool_input

                # call appropriate tool
                if func == "create_folder":
                    print("Creating folder...", tinput_obj, 'tinput object')
                    obs = create_folder_tool(project_root, tinput_obj)
                elif func == "write_file":
                    print("Writing file...", tinput_obj, 'tinput object')
                    obs = write_file_tool(project_root, tinput_obj)
                else:
                    obs = f"ERROR: Unknown function '{func}'"

            except Exception as e:
                obs = f"ERROR executing tool {func}: {e}\n{traceback.format_exc()}"

            print("🔧 TOOL:", obs)

            # append observation and loop
            messages.append({"role": "assistant", "content": json.dumps({"step": "observe", "content": obs})})
            continue

        elif step == "observe":
            # model observed result of previous tool; display and continue
            print("OBSERVE:", content)
            continue

        elif step == "result":
            print("RESULT:", content)
            print("\nDone. Project created at:", project_root)
            # append final assistant message then break
            messages.append({"role": "assistant", "content": json.dumps(parsed)})
            break

        else:
            print("ERROR: Unknown step returned by model:", step)
            print("Full parsed:", parsed)
            break

if __name__ == "__main__":
    try:
        run_interactive()
    except KeyboardInterrupt:
        print("\nInterrupted.")