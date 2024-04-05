#!/usr/bin/env python3

import asyncio
import hashlib
import concurrent.futures
import functools
import subprocess
import requests

import pbzx
import plistlib
import shutil
from pathlib import Path

SESSION = requests.session()
async def get_size(url):
    response = SESSION.head(url)
    size = int(response.headers['Content-Length'])
    return size


def download_range(url, start, end, output):
    headers = {'Range': f'bytes={start}-{end}'}
    response = SESSION.get(url, headers=headers)

    with open(output, 'wb') as f:
        for part in response.iter_content(1024):
            f.write(part)


async def download(run, url, hashes, extracted_manifest_file_path='', chunk_size=104857600):
    output_path = 'out/package'

    file_hashes = {}

    if url:
        file_size = await get_size(url)
        chunks = range(0, file_size, chunk_size)

        tasks = [
            run(
                download_range,
                url,
                start,
                start + chunk_size - 1,
                f'{output_path}.pkg.part{i}',
            )
            for i, start in enumerate(chunks)
        ]

        await asyncio.wait(tasks)

        if 'sha1' in hashes:
            sha1 = hashlib.sha1()
        if 'md5' in hashes:
            md5 = hashlib.md5()
        if 'sha2-256' in hashes:
            sha256 = hashlib.sha256()

        with open(f'{output_path}.pkg', 'wb') as o:
            for i in range(len(chunks)):
                chunk_path = f'{output_path}.pkg.part{i}'

                with open(chunk_path, 'rb') as s:
                    file_contents = s.read()
                    if 'sha1' in hashes:
                        sha1.update(file_contents)
                    if 'md5' in hashes:
                        md5.update(file_contents)
                    if 'sha2-256' in hashes:
                        sha256.update(file_contents)
                    o.write(file_contents)

                Path(chunk_path).unlink()

        if 'sha1' in hashes:
            file_hashes['sha1'] = sha1.hexdigest()
        if 'md5' in hashes:
            file_hashes['md5'] = md5.hexdigest()
        if 'sha2-256' in hashes:
            file_hashes['sha2-256'] = sha256.hexdigest()

    manifest_content = {}

    if extracted_manifest_file_path:
        pkg_expand = subprocess.run(['pkgutil', '--expand', f'{output_path}.pkg', output_path])
        pkg_expand.check_returncode()
        base_file = 'Payload'
        is_compressed = pbzx.extract_file(f'{output_path}/{base_file}', f'{output_path}/{base_file}_expanded')
        if is_compressed:
            base_file = f'{base_file}_expanded'
        with open(f'{output_path}/{base_file}', 'rb') as payload_file:
            cpio_response = subprocess.run(['cpio', '-id', f'./{extracted_manifest_file_path}'], stdin=payload_file, cwd=output_path, stderr=subprocess.DEVNULL)
            cpio_response.check_returncode()

            manifest_content = plistlib.loads(Path(f'{output_path}/{extracted_manifest_file_path}').read_bytes())
        shutil.rmtree(output_path)

    Path(f'{output_path}.pkg').unlink()

    return (file_hashes, manifest_content)

def handle_pkg_file(download_link=None, hashes=None, extracted_manifest_file_path=None):
    if hashes is None:
        hashes = ['sha1']
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    loop = asyncio.new_event_loop()
    run = functools.partial(loop.run_in_executor, executor)

    asyncio.set_event_loop(loop)

    try:
        (file_hashes, manifest) = loop.run_until_complete(
            download(run, download_link, hashes, extracted_manifest_file_path)
        )
        return (file_hashes, manifest)
    finally:
        loop.close()