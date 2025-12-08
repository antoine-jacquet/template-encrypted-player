# Encrypted Strategy Player Template

Use this template when you want a public repository (free GitHub Actions minutes) without publishing your penalty-shootout strategy. Only an encrypted payload lives in git; the workflow decrypts it just-in-time, submits your move, then deletes the plaintext.

## 1. Quick Start Checklist

1. **Fork this repository** – Fork it to your own GitHub account so GitHub Actions can run your player automatically.

2. **Add repository secrets** – In **Settings → Secrets and variables → Actions** create:
   - `PLAYER_NAME` – the public name you want the server to display
   - `SERVER_URL` – the base UBX server URL
   - `GAME_TOKEN` – a fine-grained GitHub Personal Access Token with:
     - **Repository access**: Only your player repository (select the specific repo)
     - **Repository permissions** (all set to Read and write):
       - `Actions: Read and write` (required - to trigger workflows via repository_dispatch)
       - `Workflows: Read and write` (required - for workflow management)
       - `Contents: Read and write` (required - for repository access)

3. **Set up GPG encryption** (one-time setup):
   
   a. **Create a GPG key and export it:**
   ```bash
   gpg --quick-generate-key "YOUR NAME (penalty bot)" rsa4096 sign,encrypt 1y
   gpg --armor --export-secret-keys "YOUR NAME (penalty bot)" > private-key.asc
   base64 private-key.asc > private-key.asc.b64
   ```
      When creating the key, enter a passphrase (remember it for step 3b).
   
   b. **Add GPG secrets to GitHub:**
      - In **Settings → Secrets and variables → Actions**, add:
        - `GPG_PRIVATE_KEY_B64` – paste the contents of `private-key.asc.b64`
        - `GPG_PASSPHRASE` – the passphrase you entered when creating the GPG key
      - **Security:** Delete `private-key.asc` and `private-key.asc.b64` from your local machine after copying.

4. **Encrypt your strategy and commit** (required):
   - Edit `strategy.py` with your strategy logic (or keep the default random strategy)
   - Run: `python scripts/setup_encryption.py --recipient "YOUR NAME (penalty bot)"`
   - The script will encrypt `strategy.py` and create `strategy.py.gpg`
   - Run `git restore strategy.py` or `git stash` to remove the plaintext `strategy.py` from your working directory
   - Commit `strategy.py.gpg` and all other template files (`.github/workflows/`, `register.py`, `bot.py`, `requirements.txt`, etc.)
   - **Do NOT commit:** `strategy.py` (plaintext), `private-key.asc`, or `private-key.asc.b64`
   - Push to your forked repository

## 2. Registration

Register your player by running the registration workflow via GitHub Actions:

1. Go to **Actions** tab in your repository
2. Select the **Register Player** workflow from the left sidebar
3. Click **Run workflow** → **Run workflow** button
4. The workflow will register your player using the secrets you configured

Once registered, the server will automatically trigger your workflow after each turn.

## 3. What the scripts do

The scripts interact with the game server via REST API endpoints:

- **`register.py`** – Validates required secrets, reads `PLAYER_NAME` from the environment, and sends a POST request to `/register` with your player name and repository information. The server authenticates using your `GAME_TOKEN` and stores your player configuration.

- **`bot.py`** – Executes your game strategy:
  - Decrypts `strategy.py.gpg` to `strategy.py` (handled by the workflow)
  - Sends a GET request to `/status?player_name=<PLAYER_NAME>` to retrieve the current game state (turn, opponents, history), where `<PLAYER_NAME>` is the value from your `PLAYER_NAME` secret
  - Calls your `strategy(state)` function with the game state
  - Sends a POST request to `/action` with your chosen `shoot` and `keep` directions for each opponent
  - Cleans up the decrypted `strategy.py` file
  
  Customise your strategy by editing the `strategy(state)` function in `strategy.py` to analyze the game state and return action directions. The function must return the dictionary format described below.

## 4. Understanding the `/status` payload

`/status` responds with a JSON dictionary—`{}` at the very beginning of a fresh game—that contains:

- `playerIds`: every registered player ID (these are what you target in your action maps).
- `myPlayerId`: the ID associated with your GitHub token.
- `opponentsIds`: convenience list of all other IDs.
- `state`: a list where each entry records one completed turn. Penalty shootout rounds look like:
  ```json
  [
    {
      "_turnId": 1,
      "player-id-A": {
        "player-id-B": { "shoot": 2, "keep": 0, "outcome": true },
        "player-id-C": { "shoot": 0, "keep": 1, "outcome": false }
      },
      "player-id-B": {
        "player-id-A": { "shoot": 1, "keep": 2, "outcome": false },
        "player-id-C": { "shoot": 2, "keep": 0, "outcome": true }
      },
      "player-id-C": {
        "player-id-A": { "shoot": 0, "keep": 1, "outcome": true },
        "player-id-B": { "shoot": 1, "keep": 2, "outcome": false }
      }
    },
    {
      "_turnId": 2,
      "...": { "...": "..." }
    }
  ]
  ```
  In this snapshot, `state[0]["player-id-A"]["player-id-B"]` summarizes the penalty with A shooting and B keeping in the first turn: A shot right (`2`), B dived left (`0`), and `outcome` is `true` (goal scored).
- `turnId`: the current turn number (metadata describing where the match is).

Store or inspect this data to drive smarter strategies.

## 5. Building the action payload

Your `strategy(state)` function must return a dictionary with two maps, one for shooting and one for keeping. For example, if the server identifies you as `"player-A"` and you face opponents `"player-B"` and `"player-C"`, one admissible return value is

```json
{
  "shoot": { "player-B": 2, "player-C": 0 },
  "keep":  { "player-B": 1, "player-C": 1 }
}
```
where
- `shoot` lists the direction (integers `0`, `1`, or `2`) you will shoot against each opponent.
- `keep` lists the direction you will guard against each opponent.
- Opponent IDs come straight from `playerIds`/`opponentsIds` in the `/status` payload.

`bot.py` already turns this dictionary into the HTTP payload, so you do not need to worry about the outer structure—just return the maps above.

## 6. Safety notes

- Never commit the plaintext `strategy.py` or raw private key files (`private-key.asc`, `private-key.asc.b64`).
- Rotate your GPG key periodically and refresh the GitHub secrets.
- Avoid printing secrets—workflow logs are visible to anyone with repo access.
- The workflow automatically cleans up the decrypted `strategy.py` file after each run.

Once you add your secrets and encrypted payload, the server will automatically trigger your workflow after each turn, allowing you to keep your repository public (free GitHub Actions) while keeping your strategy private.
