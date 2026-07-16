#!/usr/bin/env python3

import asyncio
import hashlib
import concurrent.futures
import functools
import plistlib
import shutil
from pathlib import Path
import subprocess
import pbzx
import requests


SESSION = requests.session()
async def get_size(url):
    response = SESSION.head(url)
    size = int(response.headers['Content-Length'])
    return size


def download_range(url, start, end, output):
    if Path(output).exists(): return
    headers = {'Range': f'bytes={start}-{end}'}
    response = SESSION.get(url, headers=headers, timeout=30)

    with open(output, 'wb') as f:
        for part in response.iter_content(1024):
            f.write(part)


async def download(run, url, hashes, output_path, chunk_size=104857600):
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
                f'{output_path}.part{i}',
            )
            for i, start in enumerate(chunks)
        ]

        if not tasks:
            return {}
        await asyncio.wait(tasks)

        if 'sha1' in hashes:
            sha1 = hashlib.sha1()
        if 'md5' in hashes:
            md5 = hashlib.md5()
        if 'sha2-256' in hashes:
            sha256 = hashlib.sha256()

        for i in range(len(chunks)):
            if not Path(f'{output_path}.part{i}').exists():
                return await download(run, url, hashes, output_path, chunk_size)

        with open(output_path, 'wb') as o:
            for i in range(len(chunks)):
                chunk_path = f'{output_path}.part{i}'

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

    return file_hashes

def handle_ota_file(download_link, key, aea_support_file='aastuff', only_manifest=False, extract_file=True):
    file_path = f'otas/{download_link.split("/")[-1]}'
    output_path = file_path.split('.')[0]
    remove_input_file = False
    remove_output_file = False
    if only_manifest:
        remove_output_file = True
        Path(f"{output_path}/AssetData/boot/").mkdir(parents=True, exist_ok=True)
        subprocess.run([f'./{aea_support_file}', '-i', download_link, '-o', output_path, '-k', key, "-e", "-f", "AssetData/boot/BuildManifest.plist"], check=True, stderr=subprocess.DEVNULL)
    else:
        if not Path(file_path).exists():
            remove_input_file = True
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
            loop = asyncio.new_event_loop()
            run = functools.partial(loop.run_in_executor, executor)

            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(
                    download(run, download_link, [], file_path)
                )
            finally:
                loop.close()

        if extract_file and not Path(output_path).exists():
            remove_output_file = True
            subprocess.run([f'./{aea_support_file}', '-i', file_path, '-o', output_path, '-k', key], check=True, stderr=subprocess.DEVNULL)
            if remove_input_file:
                Path(file_path).unlink(missing_ok=True)
    return remove_output_file

def handle_pkg_file(download_link=None, hashes=None, extracted_manifest_file_path=None, file_suffix=None, remove_file=True):
    if hashes is None:
        hashes = ['sha1']
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    loop = asyncio.new_event_loop()
    run = functools.partial(loop.run_in_executor, executor)

    asyncio.set_event_loop(loop)
    output_path = 'out/package'
    if file_suffix:
        output_path = f"{output_path}{file_suffix}"

    try:
        file_hashes = loop.run_until_complete(
            download(run, download_link, hashes, f"{output_path}.pkg")
        )
    finally:
        loop.close()

    manifest_content = {}

    if extracted_manifest_file_path:
        payload_path = f"{output_path}/Payload"
        try:
            subprocess.run(['pkgutil', '--expand-full', f'{output_path}.pkg', output_path], check=True)
        except FileNotFoundError:
            subprocess.run(["7z", "x", "-txar", "-bso0", "-bsp0", f'-o{output_path}', f'{output_path}.pkg', "Payload"], check=True)
            is_compressed = pbzx.extract_file(f'{payload_path}', f'{payload_path}_expanded')
            payload_file = 'Payload'
            if is_compressed:
                payload_file = 'Payload_expanded'
                payload_path = f'{payload_path}_expanded'
            Path(payload_path).move(f"{payload_path}.gz")
            gz_output = subprocess.run(["gunzip", "-f", f"{payload_file}.gz"], cwd=output_path, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            subprocess.run(["cpio", "-i"], input=gz_output.stdout, cwd=output_path, stderr=subprocess.DEVNULL)
            payload_path = output_path
        manifest_content = plistlib.loads(Path(f'{payload_path}/{extracted_manifest_file_path}').read_bytes())
        shutil.rmtree(output_path)

    if remove_file:
        Path(f'{output_path}.pkg').unlink(missing_ok=True)
    return (file_hashes, manifest_content)