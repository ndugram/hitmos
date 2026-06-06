<p align="center">
  <img src="https://raw.githubusercontent.com/ndugram/hitmos/master/docs/logo.png" style="background:white; padding:12px; border-radius:10px; width:300">
</p>
<p align="center">
    <em>AI terminal assistant powered by OpenRouter — minimal, fast, developer UX.</em>
</p>
<p align="center">
<a href="https://pypi.org/project/hitmos" target="_blank">
    <img src="https://img.shields.io/pypi/v/hitmos?color=%2300d7af&label=pypi%20package" alt="Package version">
</a>
<a href="https://pypi.org/project/hitmos" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/hitmos.svg?color=%2300d7af" alt="Supported Python versions">
</a>
<a href="https://pypi.org/project/hitmos" target="_blank">
    <img src="https://img.shields.io/pypi/dm/hitmos?color=%2300d7af&label=downloads" alt="Monthly downloads">
</a>
<a href="https://pepy.tech/projects/hitmos" target="_blank">
    <img src="https://img.shields.io/pepy/dt/hitmos?color=%2300d7af&label=total%20downloads" alt="Total downloads">
</a>
<a href="https://github.com/ndugram/hitmos" target="_blank">
    <img src="https://img.shields.io/github/stars/ndugram/hitmos?style=social" alt="GitHub Stars">
</a>
</p>

---

**Source Code**: <a href="https://github.com/ndugram/hitmos" target="_blank">https://github.com/ndugram/hitmos</a>

---

Hitmos is a modern **AI terminal assistant** for developers, powered by <a href="https://openrouter.ai" target="_blank">OpenRouter</a>. It brings a Claude Code–styled UX to your terminal — live markdown streaming, interactive model switching, project context injection, and Tab completion, all with zero latency overhead.

Key features:

- **Streaming** — responses stream token-by-token with live Markdown rendering via <a href="https://github.com/Textualize/rich" target="_blank">rich</a>.
- **Multi-model** — switch between DeepSeek, Gemini, Claude, GPT-4o, Llama, and more with an interactive arrow-key picker.
- **Project context** — automatically injects your project files into the system prompt so the model can answer project-specific questions.
- **Tab completion** — `/model <Tab>` lists all available models; `/` completes all commands.
- **Minimal UX** — Claude Code–inspired welcome panel, `◆` status lines, clean `>` prompt.
- **Fast** — built on <a href="https://github.com/ndugram/fasthttp" target="_blank">fasthttp-client</a> with full async SSE streaming.
- **Configurable** — API key via env (`OPEN_TOKEN`, `OPENROUTER_API_KEY`) or `~/.hitmos/config.toml`.

## Requirements

Python 3.13+

Hitmos depends on:

- <a href="https://github.com/ndugram/fasthttp" target="_blank"><code>fasthttp-client</code></a> — async HTTP transport with SSE streaming.
- <a href="https://github.com/Textualize/rich" target="_blank"><code>rich</code></a> — live Markdown rendering and styled console output.
- <a href="https://typer.tiangolo.com/" target="_blank"><code>typer</code></a> — CLI interface.
- <a href="https://github.com/ijl/orjson" target="_blank"><code>orjson</code></a> — fast JSON parsing.
- <a href="https://github.com/prompt-toolkit/python-prompt-toolkit" target="_blank"><code>prompt-toolkit</code></a> — async input with Tab completion (bundled with questionary).
- <a href="https://github.com/tmbo/questionary" target="_blank"><code>questionary</code></a> — interactive model picker.
- <a href="https://docs.pydantic.dev/" target="_blank"><code>pydantic-settings</code></a> — config management.

## Installation

```console
$ pip install hitmos

---> 100%
```

## Quickstart

### Save your API key

```console
$ hitmos login
```

Or set an environment variable:

```console
$ export OPEN_TOKEN=sk-or-...
```

### Start chatting

```console
$ hitmos
```

You will see:

```
╭─────────────────────────────────────────────────────╮
│                                                     │
│  ✻  Welcome to Hitmos                               │
│                                                     │
│  /help for commands                                 │
│                                                     │
╰─────────────────────────────────────────────────────╯

 ◆ ~/my-project
 ◆ deepseek/deepseek-chat
 ◆ context 12 KB

>
```

Ask anything about your project:

```
> what does this project do?
> add error handling to client.py
> explain the streaming logic
```

## Commands

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/model` | Interactive model picker (↑↓ + Enter) |
| `/model <name>` | Switch model directly |
| `/clear` | Clear conversation history |
| `/reset` | Reset context |
| `/exit` | Exit Hitmos |

### Switch model interactively

Type `/model` and press Enter to open the arrow-key picker:

```
? Select model  (↑↓ navigate, Enter confirm, Ctrl+C cancel)
❯ deepseek/deepseek-chat                   DeepSeek Chat · fast, cheap, great for code
  deepseek/deepseek-r1                     DeepSeek R1 · reasoning model
  google/gemini-2.5-flash                  Gemini 2.5 Flash · fast multimodal
  google/gemini-2.5-pro                    Gemini 2.5 Pro · powerful multimodal
  anthropic/claude-3.5-haiku               Claude 3.5 Haiku · fast Anthropic
  anthropic/claude-sonnet-4-5              Claude Sonnet 4.5 · balanced Anthropic
  openai/gpt-4o-mini                       GPT-4o Mini · OpenAI fast
  openai/o4-mini                           o4-mini · OpenAI reasoning
  meta-llama/llama-3.3-70b-instruct        Llama 3.3 70B · open source
  mistralai/mistral-small-3.2-24b-instruct Mistral Small 3.2 · lightweight
```

Or use Tab completion: type `/model deep` then press `Tab`.

## Configuration

Hitmos resolves the API key in this order:

1. `OPEN_TOKEN` environment variable
2. `OPENROUTER_API_KEY` environment variable
3. `~/.hitmos/config.toml`

Config file format:

```toml
token = "sk-or-..."
model = "deepseek/deepseek-chat"
```

## Contributing

Contributions are welcome! Please open an issue or pull request on <a href="https://github.com/ndugram/hitmos" target="_blank">GitHub</a>.

## License

This project is licensed under the terms of the <a href="https://github.com/ndugram/hitmos/blob/master/LICENSE" target="_blank">MIT license</a>.
