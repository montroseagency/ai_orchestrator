#!/usr/bin/env python3
"""
IDE MCP Server — Exposes deep IDE intelligence to Claude Code.
Provides tools: get_git_diff, find_references, run_ide_linter.
"""
from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# -- Config --
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

server = Server("ide-tools")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_git_diff",
            description="Get the git diff of uncommitted changes in the repository to understand current work context.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="find_references",
            description="Find all references/usages of a specific symbol in the project using fast text search.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The exact name of the function, variable, or class to find."
                    },
                    "directory": {
                        "type": "string",
                        "description": "Optional directory to restrict search to, e.g. 'Montrroase_website/client'"
                    }
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="run_ide_linter",
            description="Run native IDE linters (ruff for Python, eslint for TS) on a file and get structured squiggly-line feedback.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Relative path to the file to lint. e.g. 'Montrroase_website/server/api/urls.py'"
                    }
                },
                "required": ["filepath"],
            },
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "get_git_diff":
        return await _get_git_diff(arguments)
    if name == "find_references":
        return await _find_references(arguments)
    if name == "run_ide_linter":
        return await _run_ide_linter(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def _get_git_diff(args: dict) -> list[TextContent]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "diff", "--unified=3", "HEAD",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT)
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return [TextContent(type="text", text=f"Git diff failed: {stderr.decode()}")]
        diff = stdout.decode().strip()
        if not diff:
            return [TextContent(type="text", text="No uncommitted changes.")]
        return [TextContent(type="text", text=diff)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error running git diff: {e}")]

async def _find_references(args: dict) -> list[TextContent]:
    symbol = args["symbol"]
    directory = args.get("directory", "")
    target_dir = str(PROJECT_ROOT / directory) if directory else str(PROJECT_ROOT)
    
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "grep", "-n", symbol, target_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT)
        )
        stdout, stderr = await proc.communicate()
        res = stdout.decode().strip()
        if not res and proc.returncode != 0:
            return [TextContent(type="text", text=f"No references found for `{symbol}` in `{target_dir}`.")]
        return [TextContent(type="text", text=res[:4000] + ("\n... (truncated)" if len(res) > 4000 else ""))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error finding references: {e}")]

async def _run_ide_linter(args: dict) -> list[TextContent]:
    filepath = args["filepath"]
    full_path = PROJECT_ROOT / filepath
    
    if not full_path.exists():
        return [TextContent(type="text", text=f"File not found: {filepath}")]
        
    ext = full_path.suffix.lower()
    
    try:
        if ext == ".py":
            proc = await asyncio.create_subprocess_exec(
                "python", "-m", "ruff", "check", str(full_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(PROJECT_ROOT)
            )
            stdout, _ = await proc.communicate()
            res = stdout.decode().strip()
            if proc.returncode == 0 and not res:
                return [TextContent(type="text", text="No lint errors found!")]
            return [TextContent(type="text", text=f"Ruff Lint Output:\n{res}")]
            
        elif ext in [".ts", ".tsx", ".js", ".jsx"]:
            proc = await asyncio.create_subprocess_exec(
                "npx", "eslint", str(full_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(PROJECT_ROOT)
            )
            stdout, _ = await proc.communicate()
            res = stdout.decode().strip()
            if proc.returncode == 0 and "error" not in res.lower():
                return [TextContent(type="text", text="No lint errors found!")]
            return [TextContent(type="text", text=f"ESLint Output:\n{res}")]
            
        else:
            return [TextContent(type="text", text=f"No configured linter for extension {ext}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error running linter: {e}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )

if __name__ == "__main__":
    asyncio.run(main())
