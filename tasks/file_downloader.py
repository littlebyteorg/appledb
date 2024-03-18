#!/usr/bin/env python3

import hashlib
import plistlib
from pathlib import Path
import subprocess
import shutil
import pbzx

import requests

SESSION = requests.session()

def handle_pkg_file(download_link=None, hashes=['sha1'], extracted_manifest_file_path=None):
    sha1 = None
    md5 = None
    sha256 = None
    if 'sha1' in hashes:
        sha1 = hashlib.sha1()
    if 'md5' in hashes:
        md5 = hashlib.md5()
    if 'sha2-256' in hashes:
        sha256 = hashlib.sha256()

    file_hashes = {}

    output_path = 'out/package'

    if download_link:
        with SESSION.get(download_link, stream=True) as r:
            r.raise_for_status()
            with open(f'{output_path}.pkg', 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    
    with open(f'{output_path}.pkg', 'rb') as f:
        file_contents = f.read()
        if 'sha1' in hashes:
            sha1.update(file_contents)
        if 'md5' in hashes:
            md5.update(file_contents)
        if 'sha2-256' in hashes:
            sha256.update(file_contents)
    
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