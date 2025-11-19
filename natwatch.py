import os
from pathlib import Path
import subprocess
import json 
from typing import List, Tuple
from datetime import datetime, UTC
import difflib

import requests

STATE_FILE = Path("/home/thkpd/workspace/state.json")
# DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1440755589843259492/Se07Ah8T65lxzEz9hyF_BKStmtyjDZ4hs6Wfkyx5dUe8EN23Ie7xuyBKIGvCta02We8P"
IPTABLES_CMD = ["iptables-save", "-t", "nat"]


def run_cmd(cmd:list)->str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Failed", e)
        
def get_nat_rules() -> List[str]:
    output=run_cmd(IPTABLES_CMD)
    lines = [line.strip() for line in output.splitlines()]
    lines = [l for l in lines if l and not l.startswith("#")]
    return lines



def load_previous_rules() -> List[str]:
    if not STATE_FILE.exists():
        return []
    
    try:
        data = json.loads(STATE_FILE.read_text())
        return data.get("rules", [])
    
    except Exception:
        return []
    
def save_current_rules(rules: List[str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "rules": rules,
        "saved_at": datetime.now(UTC).isoformat()
    }
    
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)
    
    
def diff_rules(old: List[str], new: List[str])-> Tuple[List[str], List[str]]:
    old_set = set(old)
    new_set = set(new)
    added = sorted(new_set-old_set)
    removed = sorted(old_set-new_set)
    return added, removed

def format_diff (added: List[str], removed: List[str]) -> str:
    lines = []
    if added: 
        lines.append("[+] Added rules")
        for r in added: 
            lines.append(f"```{r}```")
    
    if removed:
        lines.append("[-] Removed rules")
        for r in removed:
            lines.append(f"```{r}```")
    
    if not lines:
        return "No change in NAT table"
    return "\n".join(lines)

def format_unified(old: List[str], new:List[str])-> str:
    diff =list(difflib.unified_diff(old, new, fromfile="before", tofile="after", lineterm=""))
    if not diff:
        return ""
    text = "\n".join(diff)
    if len(text) > 1000:
        text=text[:1000] + "\n...(diff truncated)"
    return f"```diff\n{text}\n```"

def send_discord_message(msg: str)-> None:
    if not DISCORD_WEBHOOK_URL:
        print("url not set, skipping")
        print(f"message would have been {msg}")
        return
    
    payload = {"content": msg}
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if not (200 <= resp.status_code<300):
            print(f"failed to send discord message: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")
        
def main():
    now = datetime.now(UTC)
    try:
        current_rules = get_nat_rules()
    except RuntimeError as e:
        send_discord_message(f"error: {e}")
        return 
    
    previous_rules = load_previous_rules()
    
    added, removed = diff_rules(previous_rules, current_rules)
    
    if added or removed:
        summary = format_diff(added, removed)
        unified = format_unified(previous_rules, current_rules)
        msg_parts = [
            f"**NAT table change detected at** {now}",
            "",
            summary,
        ]
        if unified:
            msg_parts.append("\n**Full diff: **")
            msg_parts.append(unified)
            
        final_msg = '\n'.join(msg_parts)
        send_discord_message(final_msg)
        
    else:
        print(f"{now} No NAT changes detected.")
    
    try:
        save_current_rules(current_rules)
    except Exception as e:
        print(f"Failed to save state: {e}")
    
if __name__=="__main__":
    main()