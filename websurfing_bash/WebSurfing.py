import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import subprocess

class Web_Scraping():
    def __init__(self) -> None:
        # Set to avoid revisiting the same URL
        self.visited_urls = set()

        # Start Tor as a background process
        try:
            self.tor_process = subprocess.Popen([r".venv\Scripts\tor.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print('Starting tor.exe...')
            self.wait_for_tor_start()
        except Exception as e:
            print(f"Error starting Tor: {e}")

    def wait_for_tor_start(self, timeout=30):
        """
        Waits for Tor to be fully initialized and ready to accept requests.
        """
        time_waited = 0
        tor_started = False
        while time_waited < timeout:
            # Attempt to check if Tor is ready
            try:
                response = requests.get('https://check.torproject.org/', proxies={
                    'http': 'socks5h://127.0.0.1:9050',
                    'https': 'socks5h://127.0.0.1:9050'
                }, timeout=5)
                if "Congratulations" in response.text:
                    print("Tor is running and ready!")
                    tor_started = True
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
            time_waited += 2
        
        if not tor_started:
            print("Tor failed to start within the timeout period.")
            self.terminate_tor()

    def terminate_tor(self):
        """
        Gracefully terminates the Tor process.
        """
        if self.tor_process:
            self.tor_process.terminate()
            print("Tor process terminated.")

    def find_one_term(self, url="https://www.wikipedia.org", search_term="Wiki", dark_web=False, proxies=None):
        """
        Args:
            url (str): The URL to search in.
            search_term (str): The term to search for in the page content.
            dark_web (bool): Whether to search the dark web or not.
            proxies (dict): The proxies dictionary to route traffic through Tor (for dark web).

        Returns:
            int: 1 if the search term is found, 0 if not found.
            Exception: If a request error occurs.
        """
        if proxies is None:
            proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }

        try:
            # Make a GET request to fetch the page content
            if dark_web:
                response = requests.get(url, proxies=proxies, timeout=30)
            else:
                response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx, 5xx)

            # Parse the page content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check if the search term is in the page content
            if search_term in soup.text:
                print(f"Found the search term at: {url}")
                return 1  # Return 1 when the term is found

        except requests.exceptions.RequestException as e:
            # Handle network or HTTP request errors
            print(f"Error fetching {url}: {e}")
            return e

        return 0  # Return 0 if search term is not found

    def get_visited_sites(self):
        # Return the list of visited URLs
        return self.visited_urls

    def find_term(self, url="https://www.wikipedia.org", search_term="Wiki", max_depth=2, current_depth=0, end=True, dark_web=False, proxies=None):
        """
        Recursively searches for a term in the webpage content and follows links up to a given depth.

        Args:
            url (str): The URL to search in.
            search_term (str): The term to search for in the page content.
            max_depth (int): The maximum recursion depth.
            current_depth (int): The current depth of recursion.
            end (bool): Whether to stop after finding the term.
            dark_web (bool): Whether to search the dark web or not.
            proxies (dict): The proxies dictionary to route traffic through Tor (for dark web).

        Returns:
            int: 1 if the search term is found, 0 if not found.
            Exception: If a request error occurs.
        """
        if proxies is None:
            proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }

        # Check if the maximum depth is exceeded
        if current_depth > max_depth:
            return

        # Check if the URL has already been visited
        if url in self.visited_urls:
            return

        try:
            # Make a GET request to fetch the page content
            if dark_web:
                response = requests.get(url, proxies=proxies, timeout=30)
            else:
                response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx, 5xx)

            # Parse the page content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check if the search term is in the page content
            if search_term in soup.text:
                print(f"Found the search term at: {url}")
                if end:
                    return 1  # Return 1 to indicate the term was found and stop recursion
                else:
                    return 1  # Option to continue without terminating

            # Mark this URL as visited
            self.visited_urls.add(url)

            # Extract and follow hyperlinks from the page
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                full_url = urljoin(url, href)

                # Recursively call find_term on the new URL
                result = self.find_term(full_url, search_term, max_depth, current_depth + 1, end, dark_web, proxies)
                if result == 1:  # If the term was found in the recursive call, stop further processing
                    return 1

            # Introduce a short delay to avoid overwhelming servers
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            # Handle network or HTTP request errors
            print(f"Error fetching {url}: {e}")
            return e

        return 0  # Return 0 if the search term is not found after full recursion
    
    def __del__(self):
        # Ensure Tor process is terminated when the object is deleted
        self.terminate_tor()