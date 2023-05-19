# Milestone Monitor

## Usage
We've created a personal goal tracking chatbot called Milestone Monitor that anyone can chat with, simply by texting (number here once ready). Milestone Monitor uses GPT-powered capabilities to keep track of any goals, tasks, or habits you have, as well as send you tips and reminders regularly.

## Deploying Locally (WIP)
*Note: you will need Twilio and OpenAI accounts in order to do this*

1. Create a `.env` folder in the top directory with the following entries:
```
TWILIO_ACCOUNT_SID={Twilio account SID}
TWILIO_AUTH_TOKEN={Twilio authentication token}
MESSAGING_SERVICE_SID={Twilio messaging service SID}
REDIS_URL=redis://localhost/
POSTGRES_USER={your postgres user}
POSTGRES_PASSWORD={your postgres password}
POSTGRES_DB={your postgres database name}

OPENAI_API_KEY={OpenAI API key here}
LANGCHAIN_HANDLER=langchain
```
2. Open a terminal in this directory:
  - `cd milestone-monitor` (move into the second inner `milestone-monitor` folder)
  - `pipenv shell`
  - `pipenv install`
3. Open a second terminal, and `cd` into the inner `milestone-monitor` folder:
  - Make sure Docker Desktop is open, and run `docker-compose up`
  - `python3 manage.py migrate` (in the original terminal window)
  - `./runserver.sh` to run the server
4. Setting up ngrok:
  - Install ngrok [here](https://ngrok.com/download) if you don't already have it, and follow [these steps](https://dashboard.ngrok.com/get-started/setup) to setup
  - Instead of forwarding to port 80, use port 8000, so the last command should be `ngrok http 8000`
  - Get the forwarding URL (should be `XXXXX.ngrok-free.app`, without the `https://`), and replace it in `settings.py`
