import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import asyncio
import aiohttp
import urllib.robotparser as robotparser
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup, Comment
import re
import json


# A simple class to integrate asyncio with Tkinter
class TkinterAsyncio:
    def __init__(self, root, loop):
        self.root = root
        self.loop = loop
        self._running = False

    def run(self):
        """Starts the asyncio loop integrated with Tkinter."""
        if self._running:
            return
        self._running = True
        self._run_until_exception()

    def _run_until_exception(self):
        """Runs the asyncio loop briefly and schedules the next run."""
        if not self._running:
            return

        try:
            # Run the asyncio loop for a very short period
            self.loop.call_soon(self.loop.stop)
            self.loop.run_forever()

        except Exception as e:
            # Handle exceptions that occur in the asyncio loop
            print(f"Asyncio loop exception: {e}")
            # Consider stopping the crawl if a critical error occurs in the loop
            # self.root.after_idle(self.parent_gui.stop_crawl)

        # Schedule the next run of the asyncio loop after a small delay
        self.root.after(1, self._run_until_exception)

    def stop(self):
        """Stops the asyncio loop."""
        self._running = False
        if self.loop and self.loop.is_running():
             self.loop.stop()


class RobotsTxtCrawlerGUI:
    def __init__(self, master):
        self.master = master
        master.title("robots.txt Crawler & Data Collector")

        # --- Configuration Variables ---
        self.start_url_var = tk.StringVar()
        self.depth_var = tk.StringVar(master)
        self.delay_var = tk.DoubleVar(value=1.0)
        self.user_agent_var = tk.StringVar(value="SimpleRobotsTxtCrawler/1.0")
        self.output_dir_var = tk.StringVar(value="crawled_data")
        os.makedirs(self.output_dir_var.get(), exist_ok=True)

        # --- Data Collection Checkbox Variables ---
        self.collect_h2_var = tk.BooleanVar(value=True) # Default to True
        self.collect_h3_var = tk.BooleanVar(value=True)
        self.collect_paragraphs_var = tk.BooleanVar(value=False) # Default to False
        self.collect_images_var = tk.BooleanVar(value=True)
        self.collect_forms_var = tk.BooleanVar(value=True)
        self.collect_comments_var = tk.BooleanVar(value=False)
        self.collect_meta_tags_var = tk.BooleanVar(value=True)
        self.collect_script_sources_var = tk.BooleanVar(value=True)
        self.collect_stylesheet_sources_var = tk.BooleanVar(value=True)
        self.collect_canonical_url_var = tk.BooleanVar(value=True)
        self.collect_favicon_urls_var = tk.BooleanVar(value=True)


        # --- Input Fields ---
        ttk.Label(master, text="Starting URL:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(master, width=50, textvariable=self.start_url_var).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(master, text="Crawl Depth:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        depth_options = ["1 level", "2 levels", "3 levels", "Unlimited"]
        self.depth_var.set(depth_options[0])
        ttk.Combobox(master, textvariable=self.depth_var, values=depth_options, state="readonly").grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(master, text="Delay (seconds):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(master, width=10, textvariable=self.delay_var).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(master, text="User-Agent:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(master, width=50, textvariable=self.user_agent_var).grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(master, text="Save data to:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(master, width=50, textvariable=self.output_dir_var).grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(master, text="Browse", command=self.browse_directory).grid(row=4, column=2, padx=5, pady=5, sticky="w")

        # --- Data Collection Checkboxes Frame ---
        checkbox_frame = ttk.LabelFrame(master, text="Collect Data Options")
        checkbox_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Place checkboxes within the frame (adjust grid layout as needed)
        ttk.Checkbutton(checkbox_frame, text="H2 Tags", variable=self.collect_h2_var).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Checkbutton(checkbox_frame, text="H3 Tags", variable=self.collect_h3_var).grid(row=0, column=1, padx=5, pady=2, sticky="w")
        ttk.Checkbutton(checkbox_frame, text="Paragraphs", variable=self.collect_paragraphs_var).grid(row=0, column=2, padx=5, pady=2, sticky="w")
        ttk.Checkbutton(checkbox_frame, text="Images", variable=self.collect_images_var).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Checkbutton(checkbox_frame, text="Forms", variable=self.collect_forms_var).grid(row=1, column=1, padx=5, pady=2, sticky="w")
        ttk.Checkbutton(checkbox_frame, text="Comments", variable=self.collect_comments_var).grid(row=1, column=2, padx=5, pady=2, sticky="w")
        ttk.Checkbutton(checkbox_frame, text="Meta Tags", variable=self.collect_meta_tags_var).grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Checkbutton(checkbox_frame, text="Script Sources", variable=self.collect_script_sources_var).grid(row=2, column=1, padx=5, pady=2, sticky="w")
        ttk.Checkbutton(checkbox_frame, text="Stylesheet Sources", variable=self.collect_stylesheet_sources_var).grid(row=2, column=2, padx=5, pady=2, sticky="w")
        ttk.Checkbutton(checkbox_frame, text="Canonical URL", variable=self.collect_canonical_url_var).grid(row=3, column=0, padx=5, pady=2, sticky="w")
        ttk.Checkbutton(checkbox_frame, text="Favicon URLs", variable=self.collect_favicon_urls_var).grid(row=3, column=1, padx=5, pady=2, sticky="w")

        # Configure checkbox frame columns to expand
        checkbox_frame.grid_columnconfigure(0, weight=1)
        checkbox_frame.grid_columnconfigure(1, weight=1)
        checkbox_frame.grid_columnconfigure(2, weight=1)


        # --- Buttons ---
        self.start_button = ttk.Button(master, text="Start Crawling", command=self.start_crawl)
        self.start_button.grid(row=6, column=0, columnspan=2, pady=10) # Adjusted row
        self.stop_button = ttk.Button(master, text="Stop Crawling", command=self.stop_crawl, state=tk.DISABLED)
        self.stop_button.grid(row=7, column=0, columnspan=2, pady=5) # Adjusted row

        # --- Progress Bar ---
        self.progress = ttk.Progressbar(master, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky="ew") # Adjusted row
        self.progress["value"] = 0
        self.progress["maximum"] = 100 # Will be updated dynamically

        # --- Status Display ---
        ttk.Label(master, text="Status:").grid(row=9, column=0, padx=5, pady=5, sticky="nw") # Adjusted row
        self.status_text = scrolledtext.ScrolledText(master, height=15, width=60, state=tk.DISABLED)
        self.status_text.grid(row=10, column=0, columnspan=3, padx=5, pady=5, sticky="nsew") # Adjusted row

        # --- Grid Configuration ---
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(10, weight=1) # Adjusted row


        # --- Crawler State ---
        self.visited_urls = set()
        self.queue = []
        self.crawl_depth_limit = None
        self.is_crawling = False
        self.session = None # aiohttp ClientSession
        self.robots_cache = {} # To store parsed robots.txt for each domain
        self.crawler_task = None # To hold the main asyncio crawling task

        # --- Data Collection ---
        self.collected_data = {} # Dictionary to store data per URL
        # Instance variables to store checkbox states during a crawl
        self.collect_h2 = True
        self.collect_h3 = True
        self.collect_paragraphs = False
        self.collect_images = True
        self.collect_forms = True
        self.collect_comments = False
        self.collect_meta_tags = True
        self.collect_script_sources = True
        self.collect_stylesheet_sources = True
        self.collect_canonical_url = True
        self.collect_favicon_urls = True


        # --- Asyncio Integration ---
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.asyncio_integrator = TkinterAsyncio(root, self.loop)

        # Bind window close event to stop the asyncio loop
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)


    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)
            os.makedirs(directory, exist_ok=True) # Ensure directory exists

    def normalize_url(self, url):
        """Adds a scheme (https) if missing from the URL and removes fragments."""
        if not re.match(r'^[a-zA-Z]+://', url):
            url = 'https://' + url # Default to https
        # Remove fragment identifiers
        url, _ = urldefrag(url)
        return url

    def start_crawl(self):
        start_url_input = self.start_url_var.get().strip() # Get input and remove whitespace
        depth_str = self.depth_var.get()

        if not start_url_input:
            messagebox.showerror("Error", "Please enter a starting URL.")
            return

        # Normalize the input URL
        start_url = self.normalize_url(start_url_input)

        # Validate the normalized URL
        try:
            parsed_url = urlparse(start_url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                 messagebox.showerror("Error", f"Invalid URL format after normalization: {start_url}")
                 return
        except Exception as e:
            messagebox.showerror("Error", f"Error parsing URL: {e}")
            return


        try:
            self.delay = self.delay_var.get()
            if self.delay < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid delay value. Please enter a positive number.")
            return

        if depth_str == "Unlimited":
            self.crawl_depth_limit = float('inf')
        else:
            try:
                self.crawl_depth_limit = int(depth_str.split(" ")[0])
            except ValueError:
                 messagebox.showerror("Error", "Invalid depth value.")
                 return


        self.user_agent = self.user_agent_var.get()
        self.output_directory = self.output_dir_var.get()
        os.makedirs(self.output_directory, exist_ok=True) # Ensure output directory exists

        # --- Store checkbox states for this crawl ---
        self.collect_h2 = self.collect_h2_var.get()
        self.collect_h3 = self.collect_h3_var.get()
        self.collect_paragraphs = self.collect_paragraphs_var.get()
        self.collect_images = self.collect_images_var.get()
        self.collect_forms = self.collect_forms_var.get()
        self.collect_comments = self.collect_comments_var.get()
        self.collect_meta_tags = self.collect_meta_tags_var.get()
        self.collect_script_sources = self.collect_script_sources_var.get()
        self.collect_stylesheet_sources = self.collect_stylesheet_sources_var.get()
        self.collect_canonical_url = self.collect_canonical_url_var.get()
        self.collect_favicon_urls = self.collect_favicon_urls_var.get()
        # -------------------------------------------


        self.visited_urls = set()
        # Add the starting URL to the queue with depth 0
        self.queue = [(start_url, 0)]
        self.is_crawling = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress["value"] = 0
        self.progress["maximum"] = 0 # Will be updated as we go, set to 0 initially

        self.robots_cache = {}
        self.collected_data = {} # Reset collected data for a new crawl

        self.log_message(f"Starting crawl from: {start_url} with depth: {depth_str} and delay: {self.delay:.2f} seconds.")
        self.log_message(f"User-Agent: {self.user_agent}")
        self.log_message(f"Saving data to: {self.output_directory}")

        # Start the asyncio loop integrated with Tkinter
        self.asyncio_integrator.run()

        # Create and schedule the main crawling task
        self.loop.call_soon_threadsafe(self.create_crawler_task)


    def create_crawler_task(self):
         # This runs in the asyncio loop
         if not self.crawler_task or self.crawler_task.done():
             self.crawler_task = self.loop.create_task(self.process_queue_async())
             self.crawler_task.add_done_callback(self.on_crawler_task_done) # Add a callback


    def on_crawler_task_done(self, task):
        # This runs in the asyncio loop when the task is done
        try:
            task.result() # Check for exceptions
            self.log_message("Crawl finished.")
            self.master.after_idle(self.save_collected_data) # Save data after crawl finishes
        except asyncio.CancelledError:
             self.log_message("Crawl stopped.")
             self.master.after_idle(self.save_collected_data) # Save data even if stopped
        except Exception as e:
            self.log_message(f"Crawl finished with an error: {e}")
            self.master.after_idle(self.save_collected_data) # Attempt to save data on error
        finally:
            # Schedule GUI cleanup in the Tkinter thread
            self.master.after_idle(self.finish_crawl)


    def stop_crawl(self):
        self.is_crawling = False
        self.log_message("Attempting to stop the crawl...")
        # Cancel the task from the Tkinter thread.
        # Use call_soon_threadsafe to schedule the cancellation on the asyncio loop.
        if self.crawler_task and not self.crawler_task.done():
             self.loop.call_soon_threadsafe(self.crawler_task.cancel)

        # GUI buttons are updated in finish_crawl


    def finish_crawl(self):
        # This function runs in the Tkinter mainloop
        self.crawler_task = None
        self.is_crawling = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress["value"] = 0 # Reset progress bar

        # Close the aiohttp session gracefully
        if self.session and not self.session.closed:
             # Schedule the session close on the asyncio loop
             # Use a try-except here as run_coroutine_threadsafe can fail if loop is stopping
             try:
                 asyncio.run_coroutine_threadsafe(self.session.close(), self.loop)
             except Exception as e:
                 print(f"Error scheduling session close: {e}")
             self.session = None # Clear the reference


    async def process_queue_async(self):
        # This function runs in the asyncio event loop
        # Create session inside the async function where the loop is guaranteed to be running
        async with aiohttp.ClientSession(headers={'User-Agent': self.user_agent}) as self.session:
            processed_count = 0
            # Estimate total items to process (queue size + visited)
            # This is a rough estimate and will change dynamically
            total_estimate = len(self.queue) + len(self.visited_urls)

            # Update initial progress bar max
            self.master.after_idle(self.update_progress_max, total_estimate if total_estimate > 0 else 100)


            while self.queue and self.is_crawling:
                # Check for cancellation request
                await asyncio.sleep(0) # Allow cancellation check

                current_url, current_depth = self.queue.pop(0)

                # Update progress bar value
                processed_count += 1
                # Schedule progress update on Tkinter thread
                self.master.after_idle(self.update_progress, processed_count)


                if current_url in self.visited_urls or current_depth > self.crawl_depth_limit:
                    # log_message is already thread-safe
                    self.log_message(f"Skipping {current_url} (already visited or too deep)")
                    continue # Skip already visited or too deep URLs

                self.visited_urls.add(current_url)

                # Fetch and save robots.txt if not already done for this domain
                parsed_url = urlparse(current_url)
                domain = parsed_url.netloc
                if domain and domain not in self.robots_cache: # Ensure domain is not empty
                    await self.fetch_robots_txt_async(domain)
                    # Update total estimate after fetching robots.txt (might add new domains/URLs)
                    new_total_estimate = len(self.queue) + len(self.visited_urls)
                    # Schedule progress max update on Tkinter thread
                    self.master.after_idle(self.update_progress_max, new_total_estimate)


                # Check if crawling is allowed by robots.txt
                # Ensure the domain is in cache before checking
                # If domain is not in cache (e.g., empty domain), assume allowed for now
                if domain and domain in self.robots_cache and not self.robots_cache[domain].can_fetch(self.user_agent, current_url):
                    self.log_message(f" robots.txt disallows crawling: {current_url}")
                    continue # Skip disallowed URLs

                # Crawl the URL to find more links and collect data
                if current_depth < self.crawl_depth_limit:
                     url, new_links, page_data = await self.crawl_url_and_collect_data_async(current_url, current_depth)

                     if url and page_data:
                         self.collected_data[url] = page_data # Store collected data

                     if url and new_links:
                         for link, depth in new_links:
                              # Only add new links to the queue if not visited/queued and within depth limit
                              if link not in self.visited_urls and depth <= self.crawl_depth_limit:
                                  self.queue.append((link, depth))
                                  # Update maximum for progress bar as new items are added
                                  new_total_estimate = len(self.queue) + len(self.visited_urls)
                                  # Schedule progress max update on Tkinter thread
                                  self.master.after_idle(self.update_progress_max, new_total_estimate)


                # Respect the delay using asyncio.sleep
                await asyncio.sleep(self.delay)

            # Loop finished because queue is empty or crawling was stopped
            self.is_crawling = False # Ensure flag is set
            # on_crawler_task_done callback will handle the final cleanup


    def update_progress(self, value):
        # This function runs in the Tkinter mainloop
        # Ensure maximum is at least the current value
        if value > self.progress["maximum"]:
             self.progress["maximum"] = value
        self.progress["value"] = value

    def update_progress_max(self, maximum):
         # This function runs in the Tkinter mainloop
         # Only increase maximum if it's larger than the current max
         if maximum > self.progress["maximum"]:
             self.progress["maximum"] = maximum


    async def crawl_url_and_collect_data_async(self, url, depth):
        # This function runs in the asyncio event loop
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        new_links = []
        page_data = None # Initialize page_data

        self.log_message(f"Crawling: {url} (Depth: {depth})")

        try:
            # Use the session created in process_queue_async
            async with self.session.get(url, timeout=10) as response:
                response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # --- Data Extraction ---
                    title = soup.title.string if soup.title else "No title"

                    # Extract and normalize all links on the page
                    all_links_on_page = [link.get('href') for link in soup.find_all('a', href=True)]
                    normalized_links_on_page = []
                    for link in all_links_on_page:
                        if link:
                            try:
                                absolute_url = urljoin(url, link)
                                normalized_link, _ = urldefrag(absolute_url)
                                link_domain = urlparse(normalized_link).netloc
                                # Only consider links on the same domain for adding to the queue
                                if link_domain == domain:
                                     normalized_links_on_page.append(normalized_link)
                            except Exception as e:
                                self.log_message(f"Error processing link {link} from {url}: {e}")

                    # Get unique links on the same domain to add to the queue
                    new_links = [(link, depth + 1) for link in set(normalized_links_on_page)]


                    # Extract other data points based on checkbox selection
                    page_data = {
                        'url': url,
                        'depth': depth,
                        'title': title,
                        'links_on_page': list(set(normalized_links_on_page)), # Always collect main links
                    }

                    meta_description = soup.find('meta', attrs={'name': 'description'})
                    page_data['meta_description'] = meta_description['content'] if meta_description else "No description"

                    if self.collect_h2:
                        page_data['h2_tags'] = [h2.text for h2 in soup.find_all('h2')]
                    if self.collect_h3:
                        page_data['h3_tags'] = [h3.text for h3 in soup.find_all('h3')]
                    # Always collect H1 tags as they are fundamental
                    page_data['h1_tags'] = [h1.text for h1 in soup.find_all('h1')]


                    if self.collect_paragraphs:
                        page_data['paragraphs'] = [p.text for p in soup.find_all('p')]

                    if self.collect_images:
                        images_data = []
                        for img in soup.find_all('img'):
                            img_src = img.get('src')
                            img_alt = img.get('alt', 'No alt text')
                            if img_src:
                                 img_url = urljoin(url, img_src)
                                 images_data.append({'src': img_url, 'alt': img_alt})
                        page_data['images'] = images_data

                    if self.collect_forms:
                        forms_data = []
                        for form in soup.find_all('form'):
                            form_action = form.get('action')
                            form_method = form.get('method', 'GET').upper()
                            input_fields = []
                            for input_tag in form.find_all(['input', 'textarea', 'select']):
                                input_fields.append({
                                    'tag': input_tag.name,
                                    'type': input_tag.get('type'),
                                    'name': input_tag.get('name'),
                                    'id': input_tag.get('id'),
                                    'value': input_tag.get('value'),
                                    'placeholder': input_tag.get('placeholder')
                                })
                            forms_data.append({
                                'action': urljoin(url, form_action) if form_action else None,
                                'method': form_method,
                                'inputs': input_fields
                            })
                        page_data['forms'] = forms_data

                    if self.collect_comments:
                        page_data['comments'] = [comment.string for comment in soup.find_all(string=lambda text: isinstance(text, Comment))]

                    if self.collect_meta_tags:
                        meta_tags_data = []
                        for meta in soup.find_all('meta'):
                            meta_name = meta.get('name')
                            meta_property = meta.get('property')
                            meta_content = meta.get('content')
                            if meta_name or meta_property:
                                meta_tags_data.append({
                                    'name': meta_name,
                                    'property': meta_property,
                                    'content': meta_content
                                })
                        page_data['meta_tags'] = meta_tags_data

                    if self.collect_script_sources:
                        page_data['script_sources'] = [script.get('src') for script in soup.find_all('script', src=True)]

                    if self.collect_stylesheet_sources:
                        page_data['stylesheet_sources'] = [link.get('href') for link in soup.find_all('link', rel='stylesheet', href=True)]

                    if self.collect_canonical_url:
                        canonical_link = soup.find('link', rel='canonical')
                        canonical_url = canonical_link.get('href') if canonical_link else None
                        if canonical_url:
                             canonical_url = urljoin(url, canonical_url)
                        page_data['canonical_url'] = canonical_url

                    if self.collect_favicon_urls:
                        favicon_links = soup.find_all('link', rel=['icon', 'shortcut icon'])
                        favicon_urls = [urljoin(url, link.get('href')) for link in favicon_links if link.get('href')]
                        page_data['favicon_urls'] = favicon_urls


                    return url, new_links, page_data

                else:
                     self.log_message(f"Skipping non-HTML content at {url} (Content-Type: {content_type})")
                     return url, [], None

        except aiohttp.ClientError as e:
            self.log_message(f"Error fetching {url}: {e}")
        except Exception as e:
            self.log_message(f"Unexpected error processing {url}: {e}")
        return None, [], None

    async def fetch_robots_txt_async(self, domain):
        # This function runs in the asyncio event loop
        # Construct robots.txt URL correctly, handling http/https
        if not domain:
             self.log_message(f"Skipping robots.txt fetch for empty domain.")
             return

        # Try both http and https
        # Prioritize HTTPS
        robots_urls = [f"https://{domain}/robots.txt", f"http://{domain}/robots.txt"]

        for robots_url in robots_urls:
            try:
                # Use the session created in process_queue_async
                async with self.session.get(robots_url, timeout=5, allow_redirects=True) as response:
                    final_url = str(response.url) # Get the URL after potential redirects
                    final_domain = urlparse(final_url).netloc

                    if response.status == 200:
                        content = await response.text()
                        rp = robotparser.RobotFileParser()
                        rp.parse(content.splitlines())
                        self.robots_cache[final_domain] = rp

                        # Save the robots.txt file
                        # Sanitize domain for filename: Replace invalid characters with underscore
                        sanitized_domain = final_domain.replace('.', '_').replace(':', '_').replace('/', '_').replace('\\', '_')
                        filename = f"{sanitized_domain}-robots.txt"
                        filepath = os.path.join(self.output_directory, filename)
                        try:
                            # Ensure the directory exists before saving
                            os.makedirs(os.path.dirname(filepath), exist_ok=True)
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                            self.log_message(f"Saved robots.txt from {final_domain} to {filename}")
                        except IOError as e:
                             self.log_message(f"Error saving robots.txt for {final_domain}: {e}")
                        return # Found and processed robots.txt, exit loop

                    elif response.status == 404:
                         self.log_message(f"robots.txt not found at {robots_url}")
                         # If both failed, mark domain as having no robots.txt
                         if robots_urls.index(robots_url) == 0:
                             continue # Try HTTP if HTTPS failed
                         else:
                             rp = robotparser.RobotFileParser()
                             rp.set_url(robots_url) # Set URL for the parser
                             rp.parse([]) # Empty parse means allow all
                             self.robots_cache[final_domain] = rp
                             return # Both failed, mark as no robots.txt

                    else:
                        self.log_message(f"Error fetching robots.txt from {robots_url}: Status {response.status}")
                        if robots_urls.index(robots_url) == 0:
                             continue # Try HTTP if HTTPS failed
                        else:
                             # If both failed, assume no robots.txt and allow all (default behavior of empty parser)
                             rp = robotparser.RobotFileParser()
                             rp.set_url(robots_url)
                             rp.parse([])
                             self.robots_cache[final_domain] = rp
                             return

            except aiohttp.ClientError as e:
                self.log_message(f"Network error fetching robots.txt from {robots_url}: {e}")
                if robots_urls.index(robots_url) == 0:
                     continue # Try HTTP if HTTPS failed
                else:
                    # If both failed, assume no robots.txt
                    final_domain = urlparse(robots_url).netloc
                    rp = robotparser.RobotFileParser()
                    rp.set_url(robots_url)
                    rp.parse([])
                    self.robots_cache[final_domain] = rp
                    return
            except Exception as e:
                self.log_message(f"Unexpected error fetching robots.txt from {robots_url}: {e}")
                if robots_urls.index(robots_url) == 0:
                     continue # Try HTTP if HTTPS failed
                else:
                    # If both failed, assume no robots.txt
                    final_domain = urlparse(robots_url).netloc
                    rp = robotparser.RobotFileParser()
                    rp.set_url(robots_url)
                    rp.parse([])
                    self.robots_cache[final_domain] = rp
                    return

        # Fallback: If somehow the loop finishes without setting robots_cache
        # This shouldn't happen with the current logic, but good practice.
        initial_domain = urlparse(robots_urls[0]).netloc
        if initial_domain and initial_domain not in self.robots_cache:
            rp = robotparser.RobotFileParser()
            rp.set_url(robots_urls[0])
            rp.parse([])
            self.robots_cache[initial_domain] = rp


    def log_message(self, message):
        # This function should be callable from both Tkinter and asyncio threads.
        # Use after_idle to safely update the text widget in the Tkinter thread.
        self.master.after_idle(self._insert_log_message, message)

    def _insert_log_message(self, message):
        # This function runs in the Tkinter mainloop
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)  # Scroll to the bottom
        self.status_text.config(state=tk.DISABLED)

    def save_collected_data(self):
        # This function runs in the Tkinter mainloop
        if not self.collected_data:
            self.log_message("No data collected to save.")
            return

        output_file = os.path.join(self.output_directory, "collected_web_data.json")

        try:
            os.makedirs(self.output_directory, exist_ok=True) # Ensure directory exists
            # Convert dictionary values to a list of data entries for easier processing later
            data_to_save = list(self.collected_data.values())

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            self.log_message(f"All collected data saved to {output_file}")
        except IOError as e:
            self.log_message(f"Error saving collected data to {output_file}: {e}")
        except Exception as e:
            self.log_message(f"Unexpected error saving collected data: {e}")


    def on_closing(self):
        """Handle window closing event."""
        if self.is_crawling:
            if messagebox.askokcancel("Quit", "Crawl is in progress. Do you want to stop and quit?"):
                self.stop_crawl()
                # Give the stop operation a moment to be processed by the asyncio loop
                self.master.after(200, self._perform_closing) # Wait briefly
            # If cancel is clicked, do nothing and keep window open
        else:
            self._perform_closing()

    def _perform_closing(self):
        """Safely close the window and stop asyncio."""
        # Ensure the asyncio integrator stops its periodic calls
        self.asyncio_integrator.stop()

        # Cancel any running tasks in the asyncio loop
        if self.loop and self.loop.is_running():
            try:
                all_tasks = asyncio.all_tasks(self.loop)
                for task in all_tasks:
                    task.cancel()
                # Run the loop briefly to process cancellations
                self.loop.run_until_complete(asyncio.gather(*all_tasks, return_exceptions=True))
            except Exception as e:
                print(f"Error during asyncio task cancellation: {e}")

        # Close the aiohttp session if it exists and is not closed
        if self.session and not self.session.closed:
             try:
                 asyncio.run_coroutine_threadsafe(self.session.close(), self.loop)
             except Exception as e:
                 print(f"Error closing session: {e}")
             self.session = None

        # Close the asyncio loop
        if self.loop and not self.loop.is_closed():
             try:
                 self.loop.close()
             except Exception:
                  pass # Loop might already be closing

        # Close the Tkinter window
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    crawler_gui = RobotsTxtCrawlerGUI(root)
    root.mainloop()
