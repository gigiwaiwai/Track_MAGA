# Track_MAGA — Week 1 Macro Snapshot

Daily macro indicator tracker. Fetches 6 market signals via yfinance and outputs a Markdown report.

## Indicators

| Indicator | Ticker | Notes |
|-----------|--------|-------|
| 10Y Yield | ^TNX | Nominal, proxy for real rates |
| DXY | DX-Y.NYB | US Dollar Index |
| 5Y Yield | ^FVX | Week 1 lean |
| VIX | ^VIX | Volatility index |
| Nasdaq | ^IXIC | Nasdaq Composite |
| BTC | BTC-USD | Bitcoin |

## Setup

**Prerequisites:** Python 3.8+

```bash
git clone https://github.com/gigiwaiwai/Track_MAGA.git
cd Track_MAGA
pip install -r requirements.txt
```

## Run Once

```bash
python fetch_and_report.py
```

Output is printed to the terminal and saved to `reports/macro_YYYY-MM-DD.md`. Re-running on the same day overwrites the file (idempotent).

---

## Run Daily (Automated)

### Windows — Task Scheduler

1. Open **Task Scheduler** (search in Start menu)
2. Click **Create Basic Task** → give it a name (e.g. `Track_MAGA Daily`)
3. Trigger: **Daily** → set your preferred time (e.g. 7:00 AM)
4. Action: **Start a program**
   - Program: `python`
   - Arguments: `fetch_and_report.py`
   - Start in: `C:\explore\Track_MAGA`
5. Finish → the task will run automatically each day

To verify it's working, right-click the task and select **Run** manually the first time.

> **Tip:** To log output to a file, change the Arguments field to:
> ```
> -c "import subprocess; subprocess.run(['python', 'fetch_and_report.py'], cwd=r'C:\explore\Track_MAGA')"
> ```
> Or create a `run.bat` wrapper (see below).

#### Optional: run.bat wrapper

Create `run.bat` in the project folder:

```bat
@echo off
cd /d C:\explore\Track_MAGA
python fetch_and_report.py >> logs\run.log 2>&1
```

Then point Task Scheduler at `run.bat` instead. Create a `logs\` folder first:

```bat
mkdir logs
```

---

### macOS / Linux — cron

Open crontab:

```bash
crontab -e
```

Add a line to run at 7:00 AM every day:

```
0 7 * * * cd /path/to/Track_MAGA && python fetch_and_report.py >> logs/run.log 2>&1
```

Replace `/path/to/Track_MAGA` with your actual path.

---

### GitHub Actions (run in the cloud, free)

Create `.github/workflows/daily.yml`:

```yaml
name: Daily Macro Snapshot

on:
  schedule:
    - cron: '0 7 * * *'   # 7:00 AM UTC every day
  workflow_dispatch:        # allow manual trigger

jobs:
  snapshot:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run snapshot
        run: python fetch_and_report.py

      - name: Commit report
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add reports/
          git diff --staged --quiet || git commit -m "chore: daily snapshot $(date +%F)"
          git push
```

This runs the script daily in CI, commits the generated `.md` report back to the repo automatically — no local setup needed.

---

## Output

Reports are saved to `reports/macro_YYYY-MM-DD.md`. Example structure:

```
# Macro Snapshot - 2026-02-26

## Indicators
**10Y Yield (TNX)**: 4.05% (1D +0.4%, 5D -0.8%, 20D -4.1%) | Trend(20D): down
...

## BTC vs Nasdaq (20D)
- BTC ret20: -2.9%
- Nasdaq ret20: -2.8%
- BTC - Nasdaq (20D): -0.1%（强弱差）

## 信号提示（不做结论，仅倾向性提示）
...
```

## Project Structure

```
Track_MAGA/
├── fetch_and_report.py   # main script
├── requirements.txt      # dependencies
├── README.md
└── reports/              # auto-created, one .md per day
```
