# Modular Football Match Analyzer: Tactical Dashboard

A robust, Python-based pipeline for scraping WhoScored match event data, calculating key tactical metrics (PPDA, xT, Verticality), and generating a single, comprehensive $\text{4 x 3}$ visualization dashboard.

This project uses modular design principles, making it easy to configure for any major match URL and customize team colors without touching the core code logic.

## Project Structure

The project is divided into three core Python modules and one configuration file for clean separation of concerns:

| File           | Purpose                                                                                                                   |
| :------------- | :------------------------------------------------------------------------------------------------------------------------ |
| `scraper.py`   | Handles data acquisition (Selenium/Safari) and saves raw event data (`df_events.csv`, `matchdict.json`).                  |
| `metrics.py`   | Contains all functions for calculating tactical statistics (xT, PPDA, Progressive Passes).                                |
| `viz.py`       | Contains all plotting functions, ensuring adherence to project aesthetics.                                                |
| `dashboard.py` | The main execution script; loads config and data, calls analysis, and assembles the final $\text{4 x 3}$ dashboard image. |
| `config.json`  | Central file for setting the match URL, team names, and color palette.                                                    |

## Dashboard Features

The final output is a structured $\text{4 x 3}$ grid displaying 10 analytical plots, providing a complete match breakdown:

| Row |            Col 1 & 2            |          Col 3          |
| :-: | :-----------------------------: | :---------------------: |
|  R1 |   Starter Pass Map (Home/Away)  |   **Key Match Stats**   |
|  R2 | All-Player Pass Map (Home/Away) |   **xT Momentum Flow**  |
|  R3 |   Defensive Block (Home/Away)   | Opponent Half Pass Flow |
|  R4 |  Progressive Passes (Home/Away) |  Ball Recovery/Turnover |

## User Manual: Getting Started

### 1. Prerequisites

1. **Install Libraries:**

   ```bash
   pip install selenium beautifulsoup4 pandas matplotlib mplsoccer numpy requests
   ```
2. **Web Driver Setup (macOS/Safari):**

   * Open Safari -> Settings/Preferences.
   * Go to **Advanced** and check **"Show Develop menu in menu bar."**
   * In the Safari menu bar, click **Develop** -> **"Allow Remote Automation."**

### 2. Configuration (`config.json`)

You must edit `config.json` to define the target match details.

```json
{
    "MATCH_SETTINGS": {
        "WHOSCORED_URL": "https://www.whoscored.com/matches/1903186/live/...",
        "DATA_DIR": "./data",
        "OUTPUT_FILE_DASHBOARD": "dashboard_NEW_ARS_4x3.png"
    },
    "TEAM_COLORS": {
        "HOME_COLOR": "#43A1D5",
        "AWAY_COLOR": "#FF4C4C",
        "HOME_NAME": "Newcastle",
        "AWAY_NAME": "Arsenal"
    },
    "AESTHETICS": {
        "BG_COLOR": "#0C0D0E",
        "LINE_COLOR": "white"
    }
}
```

### 3. Execution Pipeline

Execute the files sequentially in your terminal:

**A. Create Data Directory & xT Grid (Run Once)**

```bash
mkdir data
python3 create_xt_grid.py
```

**B. Acquire Match Data**

This launches Safari and scrapes the event data based on your configuration.

```bash
python3 scraper.py
```

**C. Generate Dashboard**

This loads all data and configurations, runs the analysis, and saves the final visualization.

```bash
python3 dashboard.py
```

**Output:** The final image will be saved as `./data/dashboard_NEW_ARS_4x3.png`.
