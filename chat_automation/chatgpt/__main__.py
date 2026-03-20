import os
os.environ["NODE_NO_WARNINGS"] = "1"

import argparse
import asyncio
import sys
from pathlib import Path

from chat_automation import ChatManager, SyncChatManager
from chat_automation.verbose import set_verbose
from chat_automation.cli_common import (
    Spinner, VoiceRecorder, parse_persona, 
    load_persona, list_personas as list_personas_func
)

from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

console = Console()

SAVE_DIR = Path.home() / ".chat_automation" / "conversations"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

PERSONAS_DIR = Path(__file__).parent.parent / "personas"

HISTORY_FILE = Path.home() / ".chat_automation" / "chat_history"


class ChatGPTCLI:
    def __init__(self, verbose: bool = False, quiet: bool = False):
        self.verbose = verbose
        self.quiet = quiet

    async def export_conversation_markdown(
        self,
        conversation_id: str,
        output_file: str = None,
        group_id: str = None,
        force_reload: bool = False,
        log_network: bool = False,
        use_network: bool = True,
        dump_network_dir: str = None,
    ):
        """Export ChatGPT conversation as Markdown via browser automation"""
        import asyncio
        from pathlib import Path
        console = Console()
        if group_id:
            chat_url = f"https://chatgpt.com/g/{group_id}/c/{conversation_id}"
        else:
            chat_url = f"https://chatgpt.com/c/{conversation_id}"
        md_filename = output_file or f"chatgpt_conversation_{conversation_id}.md"
        md_path = Path(md_filename).expanduser().absolute()
        self.chat = ChatManager()
        try:
            await self.chat._ensure_browser()
            await self.chat._ensure_logged_in()

            if log_network or dump_network_dir:
                dump_dir = None
                if dump_network_dir:
                    dump_dir = Path(dump_network_dir).expanduser().absolute()
                    dump_dir.mkdir(parents=True, exist_ok=True)

                async def _log_response(response):
                    try:
                        url = response.url
                        is_interesting = (
                            conversation_id in url
                            or "/backend-api/conversation/" in url
                            or "/backend-api/conversations" in url
                        )
                        if log_network and any(
                            token in url for token in ["/backend-api/", "/conversation", "/conversations", "/history"]
                        ):
                            status = response.status
                            console.print(f"[dim]NET {status} {url}[/dim]")

                        if dump_dir and is_interesting:
                            status = response.status
                            if status < 200 or status >= 300:
                                return
                            try:
                                body = await response.text()
                            except Exception:
                                body = ""
                            max_bytes = 5 * 1024 * 1024
                            if len(body.encode("utf-8")) > max_bytes:
                                body = body.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
                            safe_name = url.replace("https://", "").replace("/", "_").replace("?", "_")
                            file_path = dump_dir / f"{status}_{safe_name}.txt"
                            file_path.write_text(body, encoding="utf-8")
                    except Exception:
                        pass

                self.chat._chatgpt.page.on("response", _log_response)
            current_url = ""
            try:
                current_url = self.chat._chatgpt.page.url or ""
            except Exception:
                current_url = ""

            if force_reload or current_url != chat_url:
                await self.chat.open_conversation_by_url(chat_url)
            else:
                console.print("[dim]Already on target conversation, skipping reload[/dim]")
            await asyncio.sleep(2)
            await self.chat._chatgpt.wait_for_ready()

            if use_network:
                try:
                    api_url = f"https://chatgpt.com/backend-api/conversation/{conversation_id}"
                    device_id = await self.chat._chatgpt.page.evaluate(
                        "() => localStorage.getItem('oai-device-id') || localStorage.getItem('oai_device_id')"
                    )
                    async def _fetch_via_page() -> str:
                        return await self.chat._chatgpt.page.evaluate(
                            "({ url, deviceId }) => fetch(url, {\n"
                            "  credentials: 'include',\n"
                            "  cache: 'no-store',\n"
                            "  headers: deviceId ? { 'oai-device-id': deviceId } : {}\n"
                            "}).then(r => r.text())",
                            {"url": api_url, "deviceId": device_id},
                        )

                    # Always navigate to ensure conversation is in session context
                    raw_text = None
                    response_event = asyncio.Event()

                    async def _capture_response(response):
                        nonlocal raw_text
                        if response.url == api_url:
                            try:
                                raw_text = await response.text()
                            except Exception:
                                raw_text = None
                            response_event.set()

                    self.chat._chatgpt.page.on("response", _capture_response)
                    try:
                        await self.chat.open_conversation_by_url(chat_url)
                        await asyncio.sleep(3)
                        await self.chat._chatgpt.wait_for_ready()
                        try:
                            await asyncio.wait_for(response_event.wait(), timeout=20)
                        except Exception:
                            pass
                    finally:
                        try:
                            self.chat._chatgpt.page.off("response", _capture_response)
                        except Exception:
                            pass

                    if raw_text is None:
                        if log_network:
                            console.print("[dim]No response body captured; trying direct fetch[/dim]")
                        session_token = await self.chat._chatgpt.page.evaluate(
                            "() => localStorage.getItem('__Secure-next-auth.session-token')"
                        )
                        if session_token:
                            api_url = f"https://chatgpt.com/backend-api/conversation/{conversation_id}?access_token={session_token}"
                        raw_text = await _fetch_via_page()
                    try:
                        import json as _json
                        data = _json.loads(raw_text)
                    except Exception:
                        data = None

                    if isinstance(data, dict) and data.get("detail"):
                        if log_network:
                            console.print("[dim]First fetch failed; retrying after short wait[/dim]")
                        await asyncio.sleep(3)
                        raw_text = await _fetch_via_page()

                    try:
                        import json as _json
                        data = _json.loads(raw_text)
                    except Exception as e:
                        raise RuntimeError(f"Failed to parse API response: {e}")

                    if isinstance(data, dict) and data.get("detail"):
                        raise RuntimeError(f"Backend API error: {data.get('detail')}")
                    if data:
                        mapping = data.get("mapping") or {}
                        current_node = data.get("current_node")

                        def _format_timestamp(ts):
                            try:
                                if ts is None:
                                    return None
                                return datetime.fromtimestamp(float(ts)).isoformat()
                            except Exception:
                                return None

                        def _extract_parts(parts):
                            texts = []
                            for part in parts:
                                if isinstance(part, str):
                                    texts.append(part)
                                elif isinstance(part, dict):
                                    part_text = part.get("text") or part.get("content")
                                    language = part.get("language") or ""
                                    if isinstance(part_text, str):
                                        if language:
                                            texts.append(f"```{language}\n{part_text}\n```")
                                        else:
                                            texts.append(part_text)
                            return "\n".join(texts).strip()

                        def _node_message(node):
                            msg = node.get("message") if node else None
                            if not msg:
                                return None
                            role = msg.get("author", {}).get("role")
                            if role not in ["user", "assistant"]:
                                return None
                            timestamp = _format_timestamp(msg.get("create_time"))
                            content = msg.get("content", {})
                            parts = content.get("parts") or []
                            text = _extract_parts(parts)
                            if not text:
                                return None
                            return {"role": role, "content": text, "timestamp": timestamp}

                        # Walk from current node back to root, then reverse
                        node_ids = []
                        node_id = current_node
                        while node_id:
                            node_ids.append(node_id)
                            node = mapping.get(node_id, {})
                            parents = node.get("parent")
                            node_id = parents if parents else None

                        node_ids.reverse()
                        messages = []
                        for node_id in node_ids:
                            node = mapping.get(node_id, {})
                            msg = _node_message(node)
                            if msg:
                                messages.append(msg)

                        if not messages:
                            raise RuntimeError("No messages found in backend API response")

                        md_parts = []
                        for msg in messages:
                            role = msg["role"]
                            timestamp = msg.get("timestamp")
                            ts_text = f" ({timestamp})" if timestamp else ""
                            header = f"## {role.upper()}{ts_text}"
                            md_parts.append(f"\n{header}\n{msg['content'].strip()}\n---\n")
                        md_export = "\n".join(md_parts)
                        with open(md_path, "w") as f:
                            f.write(md_export)
                        console.print(
                            f"[green]✓ Exported conversation '{conversation_id}' to:[/green] {md_path}"
                        )
                        return
                    if log_network:
                        console.print(f"[dim]Network error body: {raw_text[:500]}[/dim]")
                    raise RuntimeError("Backend API request failed")
                except Exception as e:
                    console.print(f"[red]Network export failed:[/red] {e}")
                    return

            # Wait for conversation messages to load (up to ~60s)
            messages_loaded = False
            for _ in range(60):
                user_msgs = await self.chat._chatgpt.page.query_selector_all(
                    "[data-testid='conversation-turn:user'], [data-message-author-role='user'], .user-message, .human-message"
                )
                assistant_msgs = await self.chat._chatgpt.page.query_selector_all(
                    "[data-testid='conversation-turn:assistant'], [data-message-author-role='assistant'], .assistant-message, .ai-message"
                )
                generic_msgs = await self.chat._chatgpt.page.query_selector_all(
                    "[data-message-id], [data-testid^='conversation-turn'], .markdown, .prose"
                )
                if user_msgs or assistant_msgs or generic_msgs:
                    messages_loaded = True
                    break
                await asyncio.sleep(1)

            if not messages_loaded:
                console.print("[yellow]Warning:[/yellow] No messages detected yet; export may be empty")
            await self.chat._chatgpt.scroll_to_top()
            await asyncio.sleep(1)
            await self.chat._chatgpt.scroll_to_bottom()
            await asyncio.sleep(1)
            # Get all message blocks (user & assistant)
            user_msgs = await self.chat._chatgpt.page.query_selector_all(
                "[data-testid='conversation-turn:user'], [data-message-author-role='user'], .user-message, .human-message"
            )
            assistant_msgs = await self.chat._chatgpt.page.query_selector_all(
                "[data-testid='conversation-turn:assistant'], [data-message-author-role='assistant'], .assistant-message, .ai-message"
            )
            messages = []
            for i in range(max(len(user_msgs), len(assistant_msgs))):
                if i < len(user_msgs):
                    user_md = (await user_msgs[i].text_content()) or ""
                    if user_md:
                        messages.append({"role": "user", "content": user_md})
                if i < len(assistant_msgs):
                    assistant_md = (await assistant_msgs[i].text_content()) or ""
                    if assistant_md:
                        messages.append({"role": "assistant", "content": assistant_md})
            # Format markdown export
            md_parts = []
            for msg in messages:
                role = msg["role"]
                header = f"## {role.upper()}"
                md_parts.append(f"\n{header}\n{msg['content'].strip()}\n---\n")
            md_export = "\n".join(md_parts)
            with open(md_path, "w") as f:
                f.write(md_export)
            console.print(f"[green]\u2713 Exported conversation '{conversation_id}' to:[/green] {md_path}")
        except Exception as e:
            console.print(f"[red]Failed to export conversation:[/red] {e}")
        finally:
            if self.chat:
                await self.chat.close()

        self.chat = None
    
    async def login(self):
        """Login to ChatGPT and save session"""
        print("=" * 70)
        print("CHATGPT LOGIN")
        print("=" * 70)
        print("\n1. Opening browser...")
        print("2. Navigate to https://chatgpt.com")
        print("3. Log in manually")
        print("4. Press Enter here when done\n")
        
        self.chat = ChatManager()
        
        try:
            # Start browser and go to ChatGPT
            await self.chat._ensure_browser()
            await self.chat._chatgpt.goto("https://chatgpt.com")
            
            print("Browser is open. Please log in now.")
            print("(Browser window should be visible)")
            print("\nPress Enter when you're logged in...")
            input()
            
            # Just verify we can access the page
            try:
                await self.chat._chatgpt.page.evaluate("document.title")
                print("\n✓ Login successful!")
            except:
                print("\n⚠ Could not verify login, but session may still be saved.")
            print(f"✓ Session saved to: ~/.config/BraveSoftware/Brave-Automation/")
            print("\nNext time you use chatgpt, you'll be already logged in.")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            if self.chat:
                await self.chat.close()
    
    async def chat_message(self, message: str, session_id: str = None, output_file: str = None):
        """Send a chat message"""
        persona_name, actual_message = parse_persona(message)
        persona_content = ""
        
        if persona_name:
            persona_content = load_persona(persona_name, PERSONAS_DIR)
            if persona_content:
                console.print(f"[dim][Persona: {persona_name}][/dim]\n")
            else:
                console.print(f"[yellow][Warning: Persona '{persona_name}' not found][/yellow]\n")
        
        self.chat = ChatManager()
        
        try:
            if session_id:
                conv_file = SAVE_DIR / f"{session_id}.json"
                if conv_file.exists():
                    await self.chat.load_conversation(str(conv_file))
                else:
                    console.print(f"[red]Session not found: {session_id}[/red]")
                    self.chat.start_conversation()
            else:
                self.chat.start_conversation()
            
            full_message = actual_message
            if persona_content:
                full_message = f"{persona_content}\n\n{actual_message}"
            
            console.print(f"[bold cyan]You:[/bold cyan] {actual_message}")
            
            if not self.quiet:
                spinner = Spinner("Thinking")
                spinner.start()
            
            response = await self.chat.send_formatted(full_message)
            
            if not self.quiet:
                spinner.stop()
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(response)
                console.print(f"[dim]Response written to: {output_file}[/dim]")
            else:
                console.print()
                console.print("[bold green]ChatGPT:[/bold green]")
                console.print(Markdown(response))
                console.print()
            
            await self.chat.export_conversation(
                str(SAVE_DIR / f"{self.chat._current_conversation.id}.json")
            )
            
            if self.chat._current_conversation.url:
                console.print(f"[dim]URL: {self.chat._current_conversation.url}[/dim]")
                console.print(f"[dim]Session ID: {self.chat._current_conversation.id}[/dim]")
                console.print(f"\n[dim]Continue with:[/dim]")
                console.print(f"[dim]  ./chatgpt continue {self.chat._current_conversation.id} \"your next message\"[/dim]")
            
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            import traceback
            traceback.print_exc()
        finally:
            if self.chat:
                await self.chat.close()
    
    async def chat_file(self, filepath: str, message: str = "", session_id: str = None, output_file: str = None):
        """Send a file"""
        if not os.path.exists(filepath):
            console.print(f"[red]Error: File not found: {filepath}[/red]")
            return
        
        self.chat = ChatManager()
        
        try:
            if session_id:
                conv_file = SAVE_DIR / f"{session_id}.json"
                if conv_file.exists():
                    await self.chat.load_conversation(str(conv_file))
            else:
                self.chat.start_conversation()
            
            console.print(f"[dim]Uploading: {filepath}[/dim]")
            if message:
                console.print(f"[dim]Message: {message}[/dim]\n")
            
            response = await self.chat.send_file(filepath, message)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(response)
                console.print(f"[dim]Response written to: {output_file}[/dim]")
            else:
                console.print()
                console.print("[bold green]ChatGPT:[/bold green]")
                console.print(Markdown(response))
                console.print()
            
            await self.chat.export_conversation(
                str(SAVE_DIR / f"{self.chat._current_conversation.id}.json")
            )
            
            console.print(f"[dim]Session: {self.chat._current_conversation.id}[/dim]")
            
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
        finally:
            if self.chat:
                await self.chat.close()
    
    async def list_conversations(self):
        """List all saved conversations"""
        console.print("[bold]" + "=" * 70 + "[/bold]")
        console.print("[bold]SAVED CONVERSATIONS[/bold]")
        console.print("[bold]" + "=" * 70 + "[/bold]\n")
        
        import json
        
        conversations = []
        for f in SAVE_DIR.glob("*.json"):
            try:
                with open(f) as file:
                    data = json.load(file)
                conversations.append({
                    'id': data.get('id', 'Unknown'),
                    'title': data.get('title', 'Untitled'),
                    'updated': data.get('updated_at', 'Unknown')[:10],
                    'messages': len(data.get('messages', [])),
                    'file': f.name
                })
            except:
                pass
        
        if not conversations:
            console.print("[dim]No saved conversations found.[/dim]")
            return
        
        conversations.sort(key=lambda x: x['updated'], reverse=True)
        
        for i, c in enumerate(conversations[:10], 1):
            console.print(f"[bold]{i}. {c['title']}[/bold]")
            console.print(f"   [dim]ID: {c['id']}[/dim]")
            console.print(f"   [dim]Messages: {c['messages']}[/dim]")
            console.print(f"   [dim]Updated: {c['updated']}[/dim]")
            console.print()
        
        if len(conversations) > 10:
            console.print(f"[dim]... and {len(conversations) - 10} more[/dim]")
    
    async def show_history(self, session_id: str = None):
        """Show conversation history"""
        console.print("[bold]" + "=" * 70 + "[/bold]")
        console.print("[bold]CONVERSATION HISTORY[/bold]")
        console.print("[bold]" + "=" * 70 + "[/bold]\n")
        
        import json
        
        if session_id:
            conv_file = SAVE_DIR / f"{session_id}.json"
            if not conv_file.exists():
                console.print(f"[red]Session not found: {session_id}[/red]")
                return
            
            with open(conv_file) as f:
                data = json.load(f)
            
            console.print(f"[bold]Title:[/bold] {data.get('title', 'Untitled')}")
            console.print(f"[bold]ID:[/bold] {data.get('id')}")
            console.print(f"[bold]Messages:[/bold] {len(data.get('messages', []))}\n")
            
            for msg in data.get('messages', []):
                role = "You" if msg['role'] == 'user' else "ChatGPT"
                content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                role_style = "cyan" if msg['role'] == 'user' else "green"
                console.print(f"[bold {role_style}]{role}:[/bold {role_style}] {content}\n")
        else:
            conversations = list(SAVE_DIR.glob("*.json"))
            if not conversations:
                console.print("[dim]No conversations found.[/dim]")
                return
            
            most_recent = max(conversations, key=lambda p: p.stat().st_mtime)
            
            with open(most_recent) as f:
                data = json.load(f)
            
            console.print(f"[bold]Most recent:[/bold] {data.get('title', 'Untitled')}")
            console.print(f"[bold]ID:[/bold] {data.get('id')}")
            console.print(f"[bold]Messages:[/bold] {len(data.get('messages', []))}\n")
            
            for msg in data.get('messages', [])[-5:]:
                role = "You" if msg['role'] == 'user' else "ChatGPT"
                content = msg['content'][:150] + "..." if len(msg['content']) > 150 else msg['content']
                role_style = "cyan" if msg['role'] == 'user' else "green"
                console.print(f"[bold {role_style}]{role}:[/bold {role_style}] {content}\n")
    
    def list_personas(self):
        """List available personas"""
        console.print("[bold]" + "=" * 70 + "[/bold]")
        console.print("[bold]AVAILABLE PERSONAS[/bold]")
        console.print("[bold]" + "=" * 70 + "[/bold]\n")
        
        personas = list_personas_func(PERSONAS_DIR)
        
        if not personas:
            console.print("[dim]No personas found in personas/ directory[/dim]")
            console.print(f"\n[dim]Create one: echo 'Your prompt' > {PERSONAS_DIR}/myrole.md[/dim]")
            return
        
        for p in personas:
            console.print(f"[bold yellow]/{p['name']}[/bold yellow]")
            console.print(f"   [dim]{p['preview']}[/dim]\n")
        
        console.print("[dim]Usage: chatgpt chat /analyst \"your question\"[/dim]")
    
    async def interactive(self, session_id: str = None):
        """Interactive REPL mode with voice support"""
        import json
        import time as time_module
        
        console.print("[bold cyan]ChatGPT Interactive Mode[/bold cyan]")
        console.print("[dim]Commands: /exit /new /save /load <id> /voice /help[/dim]")
        console.print("[dim]Press Enter twice to send message[/dim]\n")
        
        self.chat = ChatManager()
        voice = VoiceRecorder()
        
        try:
            if session_id:
                conv_file = SAVE_DIR / f"{session_id}.json"
                if conv_file.exists():
                    await self.chat.load_conversation(str(conv_file))
                    console.print(f"[dim]Loaded: {session_id}[/dim]\n")
                else:
                    console.print(f"[red]Session not found: {session_id}[/red]")
                    self.chat.start_conversation()
            else:
                self.chat.start_conversation()
            
            await self.chat._ensure_browser()
            await self.chat._ensure_logged_in()
            
            session = PromptSession(history=FileHistory(str(HISTORY_FILE)))
            buffer = []
            
            while True:
                try:
                    if buffer:
                        prompt_text = "... "
                    else:
                        prompt_text = "You: "
                    
                    line = await session.prompt_async(prompt_text, mouse_support=False)
                    
                    if line.strip() == "/exit":
                        console.print("[dim]Goodbye![/dim]")
                        break
                    
                    elif line.strip() == "/new":
                        await self.chat.new_chat()
                        buffer = []
                        console.print("[dim]Started new conversation[/dim]\n")
                        continue
                    
                    elif line.strip() == "/save":
                        await self.chat.export_conversation(
                            str(SAVE_DIR / f"{self.chat._current_conversation.id}.json")
                        )
                        console.print(f"[dim]Saved: {self.chat._current_conversation.id}[/dim]\n")
                        continue
                    
                    elif line.strip().startswith("/load "):
                        load_id = line.strip().split(None, 1)[1]
                        conv_file = SAVE_DIR / f"{load_id}.json"
                        if conv_file.exists():
                            await self.chat.load_conversation(str(conv_file))
                            buffer = []
                            console.print(f"[dim]Loaded: {load_id}[/dim]\n")
                        else:
                            console.print(f"[red]Not found: {load_id}[/red]\n")
                        continue
                    
                    elif line.strip() == "/voice":
                        console.print("Recording... Press Enter to stop")
                        if voice.start_recording():
                            await session.prompt_async("Recording... ")
                            transcript, transcribe_time = voice.stop_recording()
                            if transcript:
                                time_str = f"{transcribe_time:.1f}s" if transcribe_time > 0 else ""
                                console.print(f"[dim]Transcribed{time_str}: {transcript}[/dim]")
                                buffer.append(transcript)
                            else:
                                console.print("[red]No speech detected[/red]")
                        else:
                            console.print("[red]Failed to start recording[/red]")
                        continue
                    
                    elif line.strip() == "/help":
                        console.print("""
[dim]Commands:
  /exit        Exit interactive mode
  /new         Start new conversation
  /save        Save current conversation
  /load <id>   Load a conversation
  /voice       Record voice message
  /help        Show this help

Tips:
  - Press Enter twice to send
  - Use /persona_name to apply a persona
  - Arrow keys for history
[/dim]
""")
                        continue
                    
                    elif line.strip() == "" and buffer:
                        message = "\n".join(buffer)
                        buffer = []
                        
                        persona_name, actual_message = parse_persona(message)
                        persona_content = ""
                        
                        if persona_name:
                            persona_content = load_persona(persona_name, PERSONAS_DIR)
                            if not persona_content:
                                console.print(f"[yellow]Persona '{persona_name}' not found[/yellow]\n")
                        
                        full_message = actual_message
                        if persona_content:
                            full_message = f"{persona_content}\n\n{actual_message}"
                        
                        console.print("[dim]Sending...[/dim]")
                        response = await self.chat.send_formatted(full_message)
                        
                        if not response or response.startswith("Error"):
                            console.print(f"[red]Failed to get response: {response}[/red]")
                            continue
                        
                        console.print()
                        console.print("[bold green]ChatGPT:[/bold green]")
                        console.print(Markdown(response))
                        console.print()
                        
                        await self.chat.export_conversation(
                            str(SAVE_DIR / f"{self.chat._current_conversation.id}.json")
                        )
                        continue
                    
                    elif line.strip() == "":
                        continue
                    
                    else:
                        buffer.append(line)
                
                except KeyboardInterrupt:
                    if voice.recording_process:
                        voice.cancel_recording()
                        console.print("\n[dim]Recording cancelled[/dim]")
                    else:
                        console.print("\n[dim]Press /exit to quit[/dim]")
                    continue
                except EOFError:
                    break
            
            await self.chat.export_conversation(
                str(SAVE_DIR / f"{self.chat._current_conversation.id}.json")
            )
            
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            import traceback
            traceback.print_exc()
        finally:
            if self.chat:
                await self.chat.close()


def main():
    parser = argparse.ArgumentParser(
        description='ChatGPT CLI - Command line interface for ChatGPT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chatgpt login                              # Login to ChatGPT
  chatgpt interactive                        # Interactive REPL mode
  chatgpt chat "Explain Python decorators"   # Send a message
  chatgpt chat /analyst "Review this plan"   # Use persona
  chatgpt chat --file script.py              # Upload a file
  chatgpt personas                           # List available personas
  chatgpt list                               # List conversations
  chatgpt history                            # Show recent history
  chatgpt continue conv_2024_02_10           # Continue a conversation
  
Flags:
  -v, --verbose    Show debug output (connection status, etc.)
  -q, --quiet      Disable spinner animation
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', help='Show debug output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Disable spinner animation')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Login
    login_parser = subparsers.add_parser('login', help='Login to ChatGPT')
    
    # Chat
    chat_parser = subparsers.add_parser('chat', help='Send a message')
    chat_parser.add_argument('message', nargs='?', help='Message to send')
    chat_parser.add_argument('--file', '-f', help='File to upload')
    chat_parser.add_argument('--prompt-file', '-p', help='Read prompt from file')
    chat_parser.add_argument('--session', '-s', help='Session ID to continue')
    chat_parser.add_argument('--output', '-o', help='Write response to file (markdown format)')
    
    # List
    list_parser = subparsers.add_parser('list', help='List saved conversations')
    
    # Personas
    personas_parser = subparsers.add_parser('personas', help='List available personas')
    
    # History
    history_parser = subparsers.add_parser('history', help='Show conversation history')
    history_parser.add_argument('--session', '-s', help='Session ID to show')
    
    # Interactive
    interactive_parser = subparsers.add_parser('interactive', help='Interactive REPL mode')
    interactive_parser.add_argument('--session', '-s', help='Session ID to continue')
    
    # Continue
    continue_parser = subparsers.add_parser('continue', help='Continue a conversation')
    continue_parser.add_argument('session_id', help='Session ID to continue')
    continue_parser.add_argument('message', nargs='?', help='Message to send')
    continue_parser.add_argument('--output', '-o', help='Write response to file (markdown format)')

    # Export conversation (new)
    export_parser = subparsers.add_parser('export', help='Export conversation as markdown')
    export_parser.add_argument('conversation_id', help='Conversation URL ID (after /c/)')
    export_parser.add_argument('--group', '-g', help='Group/project ID for /g/<group_id>/c/<conversation_id> URLs')
    export_parser.add_argument('--force-reload', action='store_true', help='Force reload even if already on target URL')
    export_parser.add_argument('--log-network', action='store_true', help='Log matching network responses during export')
    export_parser.add_argument('--no-network', action='store_true', help='Disable backend API export path')
    export_parser.add_argument('--dump-network-dir', help='Write matching response bodies to this folder')
    export_parser.add_argument('--output', '-o', help='Write export to file (default: chatgpt_conversation_<id>.md)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    set_verbose(args.verbose)
    cli = ChatGPTCLI(verbose=args.verbose, quiet=args.quiet)

    if args.command == 'login':
        asyncio.run(cli.login())
    elif args.command == 'chat':
        output_file = getattr(args, 'output', None)
        if args.file:
            asyncio.run(cli.chat_file(args.file, args.message or "", args.session, output_file))
        elif args.prompt_file:
            with open(args.prompt_file, 'r') as f:
                prompt = f.read().strip()
            asyncio.run(cli.chat_message(prompt, args.session, output_file))
        elif args.message:
            asyncio.run(cli.chat_message(args.message, args.session, output_file))
        else:
            print("Error: Provide a message, --prompt-file, or --file")
    elif args.command == 'list':
        asyncio.run(cli.list_conversations())
    elif args.command == 'personas':
        cli.list_personas()
    elif args.command == 'history':
        asyncio.run(cli.show_history(args.session))
    elif args.command == 'interactive':
        asyncio.run(cli.interactive(args.session))
    elif args.command == 'continue':
        output_file = getattr(args, 'output', None)
        if args.message:
            asyncio.run(cli.chat_message(args.message, args.session_id, output_file))
        else:
            print("Error: Provide a message to continue")
    elif args.command == 'export':
        output_file = getattr(args, 'output', None)
        asyncio.run(
            cli.export_conversation_markdown(
                args.conversation_id,
                output_file,
                args.group,
                args.force_reload,
                args.log_network,
                not args.no_network,
                args.dump_network_dir,
            )
        )


if __name__ == '__main__':
    main()
