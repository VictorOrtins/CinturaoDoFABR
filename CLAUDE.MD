# Cinturão do FABR Project

## Overview

This is a Visualization-based app primarely focused on showing results and Basic/Advanced Stats about FABR, Futebol Americano Brasileiro. The idea is to fully showcase Cinturão do FABR, which is basically The Unofficial Football World Championships but for American Football in Brazil

There's already an app implemented at app/ folder where there's an UI with some data in app/data/ that already showcases what I roughly want. This was an early prototipe, before Claude, done with mostly Streamlit, and limited because of it aswell. You should use this as a guide, but you don't need to really follow what's inside of it because it has mostly a different view from what I want from this new website

## Development Process

When instructed to build a feature:
1. Use your Atlassian tools to read the feature instructions from Jira
2. Develop the feature - do not skip any step from the feature-dev 7 step process
3. Thoroughly test the feature with unit tests and integration tests and fix any issues
4. Submit a PR using your github tools

## AI Desing

When writing code to make calls to LLMs, use your Cerebras skill to use LiteLLM via OpenRoute to the gpt-oss-120b model with Cerebras as the inference provider. You should use Structured outputs so that you can interpret thre results and do what you have to do

There is an OPENROUTER_API_KEY in the .env file in the project root

## Technical design

The entire project should be package into a Docker container  
The backend should be in backed/ and be a uv project, using FastAPI  
The frontend should be in frontend/  
Document every step needed to run and stop the project locally
There should be scripts in scripts/ for:

```
scripts/start-linux.sh
scripts/stop-linux.sh
```

## Color Scheme
- Accent Yellow: #ecad0a
- Blue Primary: #209dd7
- Purple Secondary: #753991 (submit buttons or something simillar)
- Dark Navy: #032147 (headings)
- Gray Text: #888888

