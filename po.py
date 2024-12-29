import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from colorama import init, Fore

init(autoreset=True)

found_admin_panels = []

def load_admin_paths(filename):
    """Load admin paths from a file."""
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print(f"[!] Error: File {filename} not found.")
        exit(1)

def check_login_form(response_text):
    """Check for login form elements in the response."""
    soup = BeautifulSoup(response_text, 'html.parser')
    input_types = ['text', 'password']
    inputs = soup.find_all('input')
    for input_field in inputs:
        if input_field.get('type') in input_types or 'admin' in input_field.get('name', '').lower():
            return True
    return False

def check_admin_panel(url, paths):
    results = []
    if not url.startswith("http"):
        url = "http://" + url

    with requests.Session() as session:
        for path in paths:
            admin_url = f"{url}/{path}"
            for attempt in range(3): 
                try:
                    response = session.get(admin_url, timeout=5)
                    if response.status_code == 200:
                        if check_login_form(response.text):
                            results.append(admin_url)
                            print(Fore.GREEN + f"[+] Admin panel with login form found: {admin_url}")
                        break
                    elif response.status_code == 403:
                        print(Fore.YELLOW + f"[-] Access forbidden (403): {admin_url}")
                    else:
                        print(Fore.RED + f"[-] Not found or other error ({response.status_code}): {admin_url}")
                except requests.RequestException:
                    print(Fore.CYAN + f"[-] Error accessing: {admin_url}")
                    break

    return results

def check_multiple_sites(sites_file, paths, max_workers=20):
    try:
        with open(sites_file, 'r') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_admin_panel, url, paths): url for url in urls}
            for future in as_completed(futures):
                found_admin_panels.extend(future.result())
    except FileNotFoundError:
        print(f"[!] Error: File {sites_file} not found.")
        exit(1)

def save_results():
    if found_admin_panels:
        with open("result.txt", "w") as f:
            for admin_panel in found_admin_panels:
                f.write(f"{admin_panel}\n")
        print(f"[+] Results saved to result.txt")
    else:
        print("[!] No admin panels were found to save.")

def main():
    logo = r"""
			╔═╗╔═╗╦ ╦  ╔═╗╔╦╗╔╦╗╦╔╗╔  ╔═╗╦╔╗╔╔╦╗╔═╗╦═╗
			║  ╚═╗╠═╣  ╠═╣ ║║║║║║║║║  ╠╣ ║║║║ ║║║╣ ╠╦╝
			╚═╝╚═╝╩ ╩  ╩ ╩═╩╝╩ ╩╩╝╚╝  ╚  ╩╝╚╝═╩╝╚═╝╩╚═

			HELP:python3 po.py -f/--file file -p/--paths -t/--threads 
			admin.txt is default list of admin panels.
			-f/--file create a list of domain or website
         EXAMPLE:
		site.txt > domain names or websites

	  USAGE:
		python3 po.py -f sites.txt
		      
	  NOTE:
		You can leave the paths and threads because of the default.
		Then wait for the program to be finished and it will atomatically save
		the admin panel found as result.txt
			


                                  ~~~~~CSH ADMIN PANEL FINDER~~~~~
    """
    print(Fore.GREEN + logo)

    parser = argparse.ArgumentParser(description="Admin panel finder for multiple sites")
    parser.add_argument("-f", "--file", help="File containing a list of URLs", required=True)
    parser.add_argument("-p", "--paths", help="File containing a list of admin paths", default="admin.txt")
    parser.add_argument("-t", "--threads", type=int, default=20, help="Number of concurrent threads")
    args = parser.parse_args()

    admin_paths = load_admin_paths(args.paths)
    check_multiple_sites(args.file, admin_paths, args.threads)
    
    save_results()

if __name__ == "__main__":
    main()
