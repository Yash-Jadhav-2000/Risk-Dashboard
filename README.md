# 🛡️ Risk Analytics Dashboard

A Streamlit app that accepts RMS or AIR exposure data and auto-generates:
- Interactive dashboards (AAL by city/state/peril, TIV concentration, top accounts)
- AI-powered narrative risk summary via Claude API

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Expected Columns

### RMS File
| Column | Description |
|--------|-------------|
| LOCNAME / CITY | Location identifier / City name |
| WS Trv / FL Trv / FR Trv | TIV per peril |
| WS AAL / FL AAL / Total AAL | AAL per peril |

### AIR File
| Column | Description |
|--------|-------------|
| Locname / CITY | Location name / City |
| ACCNTNUM | Account number |
| WS Trv / FL Trv | TIV per peril |
| WS AAL / FL AAL / SCS AAL / Total AAL | AAL per peril |

## Features
- **Overview Tab**: Total AAL & TIV by province and city, AAL share pie chart
- **Peril Analysis Tab**: Per-peril bar charts + stacked city comparison
- **Top Accounts Tab**: Ranked accounts, TIV vs AAL scatter, loss ratio table
- **AI Summary Tab**: Claude-generated narrative covering portfolio overview + peril-wise analysis

## Notes
- Accepts CSV or Excel (.xlsx / .xls)
- Column detection is automatic based on name matching
- AI summary uses the Claude Sonnet API (requires ANTHROPIC_API_KEY in env or handled by Anthropic platform)
