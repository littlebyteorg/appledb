import json
import queue
import string
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
import requests.adapters
import urllib3

# Disable SSL warnings, because Apple's SSL is broken
urllib3.disable_warnings()
# urllib3.add_stderr_logger()

THREAD_COUNT = 16

# Preferred -> other variants
rewrite_map_v2 = {
    "https://updates.cdn-apple.com/": ["http://updates-http.cdn-apple.com/"],
    "https://mesu.apple.com/": ["http://mesu.apple.com/"],
    "https://secure-appldnld.apple.com/": ["http://appldnld.apple.com/", "http://appldnld.apple.com.edgesuite.net/content.info.apple.com/"],
    "https://download.developer.apple.com/": ["http://adcdownload.apple.com/"],
    "https://swcdn.apple.com/": ["http://swcdn.apple.com/"],
}

rewrite_map_v2_groups = [([preferred_url] + other_urls) for preferred_url, other_urls in rewrite_map_v2.items()]

# Domains that need auth
needs_auth = ["adcdownload.apple.com", "download.developer.apple.com", "developer.apple.com"]

# Domains that do not reliably support HEAD requests
no_head = ["secure-appldnld.apple.com"]

success_map = {}


def unique_list(iterable):
    return list(dict.fromkeys(iterable))


def url_host(url):
    return "/".join(url.split("/", 3)[:3]) + "/"


def appendable(iterable, url):
    if url not in iterable:
        iterable.append(url)


# We use this to set up the sort order for hosts (first the preferred hosts, then the other hosts in order)
url_host_sorted = []
for preferred_hosts, other_hosts in rewrite_map_v2.items():
    url_host_sorted.append(preferred_hosts)
    url_host_sorted.extend(other_hosts)


class ProcessFileThread(threading.Thread):
    def __init__(self, file_queue: queue.Queue, print_queue: queue.Queue, name=None):
        self.file_queue: queue.Queue = file_queue
        self.print_queue: queue.Queue = print_queue
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=10, pool_connections=16)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        # self.session_map: dict[str, requests.Session] = {}
        super().__init__(name=name)

    def run(self):
        while not self.file_queue.empty():
            try:
                ios_file = self.file_queue.get(timeout=1)
            except queue.Empty:
                # Uh empty race conditioned, nothing more to process
                break

            data = json.load(ios_file.open())

            for source in data.get("sources", []):
                links = source["links"]

                # print(f"Processing source {j+1}/{len(data['sources'])} ({((j)/len(data['sources']) * 100):.2f}%)")

                urls: list[str] = [link["url"] for link in links]
                for url in list(urls):
                    for host_group in rewrite_map_v2_groups:
                        current_host = [host for host in host_group if url.startswith(host)]
                        if current_host:
                            current_host = current_host[0]
                            for other_host in host_group:
                                if other_host != current_host:
                                    appendable(urls, url.replace(current_host, other_host))

                urls.sort(
                    key=lambda x: url_host_sorted.index(url_host(x)) if url_host(x) in url_host_sorted else len(url_host_sorted)
                )  # Sort by host order. If not in host order, put at bottom in original order

                new_links = [{"url": url, "preferred": any(url.startswith(i) for i in rewrite_map_v2), "active": False} for url in urls]

                for link in new_links:
                    url = link["url"]
                    if url in success_map:
                        # Skip ones we've already processed
                        link["active"] = success_map[url]
                        continue

                    if urlparse(url).hostname in needs_auth:
                        # We don't have credentials for this host, so we'll assume it's active and skip it
                        link["active"] = True
                        continue

                    successful_hit = False

                    resp = None

                    for _ in range(10):
                        try:
                            if urlparse(url).hostname in no_head:
                                resp = self.session.get(url, headers={"User-Agent": "softwareupdated (unknown version) CFNetwork/808.1.4 Darwin/16.1.0"}, verify=False, stream=True)
                            else:
                                resp = self.session.head(url, headers={"User-Agent": "softwareupdated (unknown version) CFNetwork/808.1.4 Darwin/16.1.0"}, verify=False, allow_redirects=True)
                        except requests.ConnectionError:
                            print("Warning: retrying connection error")
                            time.sleep(1)
                            continue
                        else:
                            break
                    else:
                        raise Exception(f"Failed to connect to {url}")

                    if urlparse(url).hostname in no_head:
                        resp.close()

                    if resp.status_code == 200:
                        successful_hit = True
                    elif resp.status_code == 403 or resp.status_code == 404:
                        # Dead link
                        successful_hit = False
                    else:  # Leave it be
                        raise Exception(f"Unknown status code: {resp.status_code}")                        

                    success_map[url] = link["active"] = successful_hit

                    if successful_hit:
                        for hdr, lcl in [("x-amz-meta-digest-sha256", "sha2-256"), ("x-amz-meta-digest-sh1", "sha1")]:
                            if hdr not in resp.headers:
                                continue

                            source.setdefault("hashes", {})[lcl] = resp.headers[hdr]

                        if "ETag" in resp.headers:
                            potential_hash = resp.headers["ETag"][1:-1]
                            if len(potential_hash) == 32 and all(c in string.hexdigits for c in potential_hash):
                                source.setdefault("hashes", {})["md5"] = potential_hash
                            else:
                                print(f"Unknown ETag type: {resp.headers['ETag']}, ignoring")

                        if "size" in source and source["size"] != int(resp.headers["Content-Length"]):
                            print(f"Warning: {ios_file.name}: Size mismatch for {url}; expected {source['size']} but got {resp.headers['Content-Length']}")

                        source["size"] = int(resp.headers["Content-Length"])
                    # self.print_queue.put("Processed a link")

                source["links"] = new_links

            json.dump(data, ios_file.open("w", newline="\n"), indent=4, ensure_ascii=False)
            self.print_queue.put(False)


class PrintThread(threading.Thread):
    def __init__(self, print_queue: queue.Queue, total: int, name=None) -> None:
        self.print_queue: queue.Queue = print_queue
        self.stop_event = threading.Event()
        self.count = 0
        self.total = total
        super().__init__(name=name)

    def run(self):
        while not self.stop_event.is_set():
            self.count += 1
            print(self.print_queue.get() or f"Processed {self.count}/{self.total} ({self.count/self.total*100}%) files")

    def stop(self):
        self.stop_event.set()


files = list(Path("iosFiles").rglob("*.json"))
file_queue = queue.Queue()
for i in files:
    file_queue.put(i)

print_queue = queue.Queue()

start = time.time()

printer_thread = PrintThread(print_queue, len(files), "Printer Thread")
printer_thread.start()

threads = [ProcessFileThread(file_queue, print_queue, name=f"Thread {i}") for i in range(THREAD_COUNT)]
for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

end = time.time()

# Done checking
printer_thread.stop()
printer_thread.join()

print(f"Processed {len(files)} files in {end-start} seconds")
