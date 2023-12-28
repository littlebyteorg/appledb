#!/usr/bin/env python3

import random
import sys
import json
import queue
import string
import threading
import time
from pathlib import Path
from typing import Collection
from urllib.parse import urlparse

import requests
import requests.adapters
import urllib3
from link_info import needs_auth, needs_apple_auth, no_head, needs_cache_bust, apple_auth_token
from sort_os_files import sort_os_file

# Disable SSL warnings, because Apple's SSL is broken
urllib3.disable_warnings()
# urllib3.add_stderr_logger()

# TODO: Make this configurable
THREAD_COUNT = 16


success_map = {}


class ProcessFileThread(threading.Thread):
    def __init__(self, file_queue: queue.Queue, print_queue: queue.Queue, use_network=True, name=None):
        self.file_queue: queue.Queue = file_queue
        self.print_queue: queue.Queue = print_queue
        self.use_network = use_network
        self.session = requests.Session()
        self.has_apple_auth = apple_auth_token != ''
        if self.has_apple_auth:
            self.session.headers = {
                "cookie": f"ADCDownloadAuth={apple_auth_token}"
            }
        adapter = requests.adapters.HTTPAdapter(max_retries=10, pool_connections=16)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        # self.session_map: dict[str, requests.Session] = {}
        super().__init__(name=name)

    def process_sources(self, sources, file_name):
        for source in sources:
            if source.get("skipUpdateLinks"):
                continue
            links = source.setdefault("links", [])
            for link in links:
                url = link["url"]
                if url in success_map:
                    # Skip ones we've already processed
                    link["active"] = success_map[url]
                    continue

                if urlparse(url).hostname in needs_auth or (urlparse(url).hostname in needs_apple_auth and not self.has_apple_auth):
                    # We don't have credentials for this host, so we'll assume it's active and skip it
                    link["active"] = True
                    continue

                if not self.use_network:
                    # Network disabled, don't touch active status
                    # link["active"] = True
                    continue

                successful_hit = False

                resp = None

                for _ in range(10):
                    try:
                        if urlparse(url).hostname in no_head:
                            resp = self.session.get(
                                url,
                                headers={"User-Agent": "softwareupdated (unknown version) CFNetwork/808.1.4 Darwin/16.1.0"},
                                verify=False,
                                stream=True,
                            )
                        else:
                            if urlparse(url).hostname in needs_cache_bust:
                                suffix = f'?cachebust{random.randint(100, 1000)}'
                            else:
                                suffix = ''
                            resp = self.session.head(
                                f"{url}{suffix}".replace('developer.apple.com/services-account/download?path=', 'download.developer.apple.com'),
                                headers={"User-Agent": "softwareupdated (unknown version) CFNetwork/808.1.4 Darwin/16.1.0"},
                                verify=False,
                                allow_redirects=True,
                            )
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
                    successful_hit = 'unauthorized' not in resp.url
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
                        # TODO: Document what server each ETag format is from
                        def is_hex(s):
                            return all(c in string.hexdigits for c in s)

                        potential_hash = resp.headers["ETag"][1:-1]

                        if len(potential_hash) == 32 and is_hex(potential_hash):
                            source.setdefault("hashes", {})["md5"] = potential_hash
                        elif len(potential_hash) > 33 and is_hex(potential_hash[:32]) and potential_hash[32] == ":":
                            # <md5>:<unix epoch>
                            # Seen on download.info.apple.com (Server: AkamaiNetStorage)
                            source.setdefault("hashes", {})["md5"] = potential_hash[:32]
                        elif len(potential_hash) > 33 and potential_hash[32] == "-":
                            # skip noise when processing large numbers of files
                            pass
                        else:
                            print(f"Unknown ETag type: {resp.headers['ETag']}, ignoring")

                    if "size" in source and source["size"] != int(resp.headers["Content-Length"]):
                        print(
                            f"Warning: {file_name}: Size mismatch for {url}; expected {source['size']} but got {resp.headers['Content-Length']}"
                        )

                    source["size"] = int(resp.headers["Content-Length"])
                # self.print_queue.put("Processed a link")
        return sources

    def run(self):
        while not self.file_queue.empty():
            try:
                ios_file = self.file_queue.get(timeout=1)
            except queue.Empty:
                # Uh empty race conditioned, nothing more to process
                break

            data = json.load(ios_file.open())

            if data.get('sources', []):
                data['sources'] = self.process_sources(data['sources'], ios_file.name)

            for entry in data.get("createDuplicateEntries", []):
                if entry.get('sources', []):
                    entry['sources'] = self.process_sources(entry['sources'], ios_file.name)

            json.dump(sort_os_file(None, data), ios_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
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
            try:
                item = self.print_queue.get(block=False)
                self.count += 1
                print(item or f"Processed {self.count}/{self.total} ({self.count/self.total*100:.2f}%) files")
            except queue.Empty:
                pass

    def stop(self):
        self.stop_event.set()


def update_links(files: Collection[Path], use_network=True):
    file_queue = queue.Queue()
    for i in files:
        file_queue.put(i)

    print_queue = queue.Queue()

    start = time.time()

    printer_thread = PrintThread(print_queue, len(files), "Printer Thread")
    printer_thread.start()

    threads = [ProcessFileThread(file_queue, print_queue, use_network, name=f"Thread {i}") for i in range(min(len(files), THREAD_COUNT))]
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    end = time.time()

    # Done checking
    printer_thread.stop()
    printer_thread.join()

    print(f"Processed {len(files)} files in {end-start} seconds")


if __name__ == "__main__":
    files = []
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            files.extend(list(Path(f"osFiles/{path}").rglob("*.json")))
    else:
        files.extend(list(Path("osFiles").rglob("*.json")))
    
    update_links(files)
