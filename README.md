# Spotify Account Checker

Automatically check Spotify accounts and determine if they are **Valid**, **Premium**, or **Free** - without login credentials!

## Features

✅ Check if email has valid Spotify account  
✅ Detect if account is **Premium** or **Free**  
✅ No login or password required  
✅ Batch process multiple emails  
✅ Export results to Excel (.xlsx) and JSON  
✅ Fast checking with built-in delays  
✅ Color-coded results (Valid/Invalid)  
✅ Summary statistics  

## Installation

1. Clone the repository:
```bash
git clone https://github.com/legendgr19826-dot/spotify-account-checker.git
cd spotify-account-checker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Setup

### Create `emails.txt`
Add email addresses to check (one per line):
```
user1@gmail.com
user2@yahoo.com
user3@outlook.com
user4@hotmail.com
```

## Usage

Run the checker:
```bash
python main.py
```

The script will:
1. Read emails from `emails.txt`
2. Check each email against Spotify API
3. Determine if account is valid
4. Identify if account is Premium or Free
5. Export results to files

## Output Files

- **spotify_results.xlsx** - Formatted Excel file with color-coded results
- **spotify_results.json** - Raw JSON data with full details
- **valid_spotify_emails.txt** - List of valid emails only

## Output Example

### Excel File
| # | Email | Status | Account Type | Details | Timestamp |
|---|-------|--------|--------------|---------|----------|
| 1 | user@gmail.com | VALID | PREMIUM | {...} | 2024-01-15 10:30:45 |
| 2 | test@yahoo.com | VALID | FREE | {...} | 2024-01-15 10:30:47 |
| 3 | fake@outlook.com | INVALID | N/A | Not found | 2024-01-15 10:30:49 |

### Console Output
```
============================================================
  SPOTIFY ACCOUNT CHECKER
  Check Valid Accounts & Premium/Free Status
============================================================

[*] Loaded 3 email(s)

[*] Checking: user@gmail.com
[+] VALID - user@gmail.com [PREMIUM]

[*] Checking: test@yahoo.com
[+] VALID - test@yahoo.com [FREE]

[*] Checking: fake@outlook.com
[-] INVALID - fake@outlook.com

============================================================
SUMMARY
============================================================
Total Checked: 3
[+] Valid Accounts: 2
    ├─ Premium: 1
    └─ Free: 1
[-] Invalid Accounts: 1
============================================================
```

## How It Works

1. **Email Validation**: Sends requests to Spotify's recovery endpoint
2. **Account Detection**: Analyzes responses to confirm account existence
3. **Type Detection**: Examines account details to determine Premium/Free status
4. **No Credentials**: Works without login/password - purely API-based

## Notes

⚠️ Respect rate limits - built-in delays between checks  
⚠️ Use responsibly  
✅ Results are saved automatically  
✅ Supports large email lists  

## Requirements

- Python 3.8+
- Internet connection
- Active Spotify accounts (to check against)

## License

MIT
