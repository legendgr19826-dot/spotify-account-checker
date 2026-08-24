import requests
import json
import time
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

class SpotifyChecker:
    def __init__(self):
        self.results = []
        self.valid_count = 0
        self.invalid_count = 0
        self.premium_count = 0
        self.free_count = 0
        
        # Headers to mimic browser request
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
        }
    
    def check_email_valid(self, email):
        """
        Check if email is valid for Spotify
        Returns: (is_valid, account_type, response_data)
        """
        try:
            # Spotify API endpoint to check if email exists
            url = 'https://www.spotify.com/api/signup/email'
            
            payload = {
                'email': email.strip().lower(),
                'send_email': False
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10,
                verify=True
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Email doesn't exist
                if data.get('status') == 1:
                    return False, None, 'EMAIL_NOT_FOUND'
                
            return False, None, f'Status: {response.status_code}'
            
        except Exception as e:
            return False, None, str(e)
    
    def check_spotify_account(self, email):
        """
        Main function to check Spotify account details
        """
        email = email.strip().lower()
        print(f"\n[*] Checking: {email}")
        
        try:
            # Method 1: Check account existence via password reset
            url = 'https://www.spotify.com/api/signup/login'
            
            payload = {
                'email': email,
                'remember': True
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10,
                allow_redirects=True
            )
            
            # Method 2: Try to get account info via public API
            # If email exists on Spotify, we can try to identify account type
            if response.status_code in [200, 400, 401, 403]:
                try:
                    data = response.json()
                except:
                    data = {}
                
                # Check if account exists based on response
                response_text = response.text.lower()
                
                # Indicators of valid account
                if 'incorrect password' in response_text or 'wrong password' in response_text:
                    account_type = self.detect_account_type(email, response)
                    return True, account_type, data
                
                elif 'email not found' in response_text or 'no account' in response_text:
                    return False, None, 'INVALID'
                
                # Try alternate method - check via account info endpoint
                return self.check_via_alternate_method(email)
            
            return False, None, 'UNKNOWN'
            
        except requests.exceptions.ConnectionError:
            print(f"[-] Connection error for {email}")
            return False, None, 'CONNECTION_ERROR'
        except Exception as e:
            print(f"[-] Error checking {email}: {str(e)}")
            return False, None, str(e)
    
    def check_via_alternate_method(self, email):
        """
        Alternate method to check account via Spotify's public endpoints
        """
        try:
            # Try to check if account exists via recover account endpoint
            url = 'https://www.spotify.com/api/auth/recover'
            
            payload = {'email': email}
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # If we get a success response, account exists
                if data.get('status') == 0:
                    # Try to determine if premium or free
                    account_type = self.determine_account_type(email, data)
                    return True, account_type, data
            
            elif response.status_code == 404:
                return False, None, 'NOT_FOUND'
            
            return False, None, f'Status: {response.status_code}'
            
        except Exception as e:
            return False, None, str(e)
    
    def detect_account_type(self, email, response):
        """
        Detect if account is Premium or Free based on response
        """
        try:
            # Check response headers and content for premium indicators
            response_text = response.text.lower()
            
            # Premium account indicators
            premium_keywords = ['premium', 'premium_plus', 'family', 'duo']
            free_keywords = ['free', 'ad', 'ads']
            
            for keyword in premium_keywords:
                if keyword in response_text:
                    return 'PREMIUM'
            
            for keyword in free_keywords:
                if keyword in response_text:
                    return 'FREE'
            
            # Default to unknown if can't determine
            return 'UNKNOWN'
        except:
            return 'UNKNOWN'
    
    def determine_account_type(self, email, data):
        """
        Determine account type from response data
        """
        try:
            if 'product' in data:
                product = data['product'].lower()
                if 'premium' in product or 'family' in product or 'duo' in product:
                    return 'PREMIUM'
                return 'FREE'
            
            if 'subscription' in data:
                if data['subscription'].lower() != 'free':
                    return 'PREMIUM'
                return 'FREE'
            
            return 'UNKNOWN'
        except:
            return 'UNKNOWN'
    
    def check_multiple_emails(self, emails_list):
        """
        Check multiple emails from list
        """
        total = len(emails_list)
        print(f"\n{'='*60}")
        print(f"Starting Spotify Account Check")
        print(f"Total emails to check: {total}")
        print(f"{'='*60}\n")
        
        for index, email in enumerate(emails_list, 1):
            email = email.strip()
            if not email or '@' not in email:
                print(f"[!] Skipping invalid email: {email}")
                continue
            
            is_valid, account_type, details = self.check_spotify_account(email)
            
            if is_valid:
                self.valid_count += 1
                status = '✓ VALID'
                
                if account_type == 'PREMIUM':
                    self.premium_count += 1
                    account_type = 'PREMIUM'
                    print(f"[+] {status} - {email} [{account_type}]")
                elif account_type == 'FREE':
                    self.free_count += 1
                    print(f"[+] {status} - {email} [{account_type}]")
                else:
                    print(f"[+] {status} - {email} [UNKNOWN]")
                
                result = {
                    'email': email,
                    'status': 'VALID',
                    'account_type': account_type,
                    'details': details,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'index': index
                }
                self.results.append(result)
            else:
                self.invalid_count += 1
                print(f"[-] INVALID - {email}")
                result = {
                    'email': email,
                    'status': 'INVALID',
                    'account_type': None,
                    'details': details,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'index': index
                }
                self.results.append(result)
            
            # Add delay to avoid rate limiting
            time.sleep(1.5)
        
        self.print_summary()
    
    def print_summary(self):
        """
        Print summary statistics
        """
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Total Checked: {self.valid_count + self.invalid_count}")
        print(f"[+] Valid Accounts: {self.valid_count}")
        print(f"    ├─ Premium: {self.premium_count}")
        print(f"    └─ Free: {self.free_count}")
        print(f"[-] Invalid Accounts: {self.invalid_count}")
        print(f"{'='*60}\n")
    
    def save_results_xlsx(self, filename='spotify_results.xlsx'):
        """
        Save results to Excel file
        """
        if not self.results:
            print("[-] No results to save")
            return
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Accounts'
        
        # Headers
        headers = ['#', 'Email', 'Status', 'Account Type', 'Details', 'Timestamp']
        ws.append(headers)
        
        # Style headers
        header_fill = PatternFill(start_color='1DB954', end_color='1DB954', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Add data
        for result in self.results:
            details_str = str(result['details'])[:100] if result['details'] else ''
            ws.append([
                result['index'],
                result['email'],
                result['status'],
                result['account_type'] or 'N/A',
                details_str,
                result['timestamp']
            ])
        
        # Color code rows
        for idx, row in enumerate(ws.iter_rows(min_row=2, max_row=len(self.results) + 1), 2):
            if self.results[idx-2]['status'] == 'VALID':
                fill_color = 'C6EFCE'  # Light green
                font_color = '006100'  # Dark green
            else:
                fill_color = 'FFC7CE'  # Light red
                font_color = '9C0006'  # Dark red
            
            for cell in row:
                cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type='solid')
                cell.font = Font(color=font_color)
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 40
        ws.column_dimensions['F'].width = 20
        
        # Add summary sheet
        ws_summary = wb.create_sheet('Summary')
        ws_summary.append(['Metric', 'Count'])
        ws_summary.append(['Total Checked', self.valid_count + self.invalid_count])
        ws_summary.append(['Valid Accounts', self.valid_count])
        ws_summary.append(['Premium Accounts', self.premium_count])
        ws_summary.append(['Free Accounts', self.free_count])
        ws_summary.append(['Invalid Accounts', self.invalid_count])
        
        # Style summary
        for cell in ws_summary[1]:
            cell.fill = header_fill
            cell.font = header_font
        
        ws_summary.column_dimensions['A'].width = 20
        ws_summary.column_dimensions['B'].width = 15
        
        wb.save(filename)
        print(f"[+] Results saved to {filename}")
    
    def save_results_json(self, filename='spotify_results.json'):
        """
        Save results to JSON file
        """
        if not self.results:
            print("[-] No results to save")
            return
        
        data = {
            'summary': {
                'total_checked': self.valid_count + self.invalid_count,
                'valid_accounts': self.valid_count,
                'premium_accounts': self.premium_count,
                'free_accounts': self.free_count,
                'invalid_accounts': self.invalid_count
            },
            'results': self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[+] Results saved to {filename}")
    
    def save_valid_only(self, filename='valid_spotify_emails.txt'):
        """
        Save only valid emails to text file
        """
        valid_emails = [r['email'] for r in self.results if r['status'] == 'VALID']
        
        if not valid_emails:
            print("[-] No valid emails to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            for email in valid_emails:
                f.write(email + '\n')
        
        print(f"[+] {len(valid_emails)} valid emails saved to {filename}")

def load_emails(filename='emails.txt'):
    """
    Load emails from file
    """
    emails = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                email = line.strip()
                if email and '@' in email:
                    emails.append(email)
    except FileNotFoundError:
        print(f"[-] File {filename} not found")
    
    return emails

def main():
    print("\n" + "="*60)
    print("  SPOTIFY ACCOUNT CHECKER")
    print("  Check Valid Accounts & Premium/Free Status")
    print("="*60)
    
    # Load emails
    emails = load_emails('emails.txt')
    
    if not emails:
        print("\n[-] emails.txt not found or empty")
        print("[*] Create emails.txt with one email per line")
        print("[*] Example:")
        print("    user1@gmail.com")
        print("    user2@yahoo.com")
        return
    
    print(f"\n[*] Loaded {len(emails)} email(s)\n")
    
    checker = SpotifyChecker()
    
    try:
        checker.check_multiple_emails(emails)
        
        # Save results
        print("\n[*] Saving results...\n")
        checker.save_results_xlsx()
        checker.save_results_json()
        checker.save_valid_only()
        
    except KeyboardInterrupt:
        print("\n[!] Process interrupted by user")
    except Exception as e:
        print(f"[-] Error: {str(e)}")

if __name__ == '__main__':
    main()
