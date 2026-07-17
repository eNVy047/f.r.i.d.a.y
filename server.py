"""
Friday MCP Server — Entry Point
Is file ko run karne ke liye use karein: python server.py ya uv run friday
"""

# FastMCP framework se FastMCP class import kar rahe hain server banane ke liye
from mcp.server.fastmcp import FastMCP

# Friday package se tools, prompts aur resources register karne wale functions import kar rahe hain
from friday.tools import register_all_tools
from friday.prompts import register_all_prompts
from friday.resources import register_all_resources

# Config file se application configurations (jaise server name) import kar rahe hain
from friday.config import config

# Yahan hum FastMCP server ka ek instance create kar rahe hain
# Isme hum config se name de rahe hain aur system instructions set kar rahe hain
mcp = FastMCP(
    name=config.SERVER_NAME, # Server ka naam config se utha rahe hain (jaise Friday)
    instructions=( # AI ko instructions de rahe hain ki use kaise behave karna hai
        "You are Friday, a Tony Stark-style AI assistant. "
        "You have access to a set of tools to help the user. "
        "Be concise, accurate, and a little witty."
    ),
)

# Sabhi custom tools ko server ke sath register kar rahe hain taaki LLM unhe call kar sake
register_all_tools(mcp)

# Sabhi standard prompts ko register kar rahe hain
register_all_prompts(mcp)

# Resources (jaise status info) ko register kar rahe hain
register_all_resources(mcp)

# Ye main function hai jo server ko run karega
def main():
    # Server ko SSE (Server-Sent Events) transport par chala rahe hain port 8000 pe default
    mcp.run(transport='sse')

# Agar ye file directly run ki gayi hai, toh main() function ko call karein
if __name__ == "__main__":
    main()