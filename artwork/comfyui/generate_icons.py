"""Generate Gunslinger icon PNGs through a running local ComfyUI API."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
import uuid


HERE = Path(__file__).resolve().parent
WIDGETS = {
    'UNETLoader': ('unet_name', 'weight_dtype'),
    'DualCLIPLoader': ('clip_name1', 'clip_name2', 'type', 'device'),
    'VAELoader': ('vae_name',),
    'CLIPTextEncode': ('text',),
    'FluxGuidance': ('guidance',),
    'ConditioningZeroOut': (),
    'EmptySD3LatentImage': ('width', 'height', 'batch_size'),
    'KSampler': ('seed', None, 'steps', 'cfg', 'sampler_name', 'scheduler', 'denoise'),
    'VAEDecode': (),
    'LoadBackgroundRemovalModel': ('bg_removal_name',),
    'RemoveBackground': (),
    'InvertMask': (),
    'JoinImageWithAlpha': (),
    'ImageScale': ('upscale_method', 'width', 'height', 'crop'),
    'SaveImage': ('filename_prefix',),
}
SAVES = {'14': ('masters', 1024), '16': ('tooltip', 380),
         '18': ('controller', 144), '20': ('hotbar', 64), '22': ('resource', 48)}


class GenerationError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> None:
        raise GenerationError(f'Unexpected API redirect to {newurl}; refusing to send prompts elsewhere.')


class ComfyClient:
    def __init__(self, base_url: str, request_timeout: float = 30) -> None:
        parsed = urlsplit(base_url)
        if (parsed.scheme != 'http' or parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in {'', '/'}):
            raise GenerationError('--url must be a local loopback HTTP address, e.g. http://127.0.0.1:8188')
        self.base_url = base_url.rstrip('/')
        self.request_timeout = request_timeout
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(self, path: str, payload: dict[str, Any] | None = None) -> bytes:
        data = None if payload is None else json.dumps(payload).encode('utf-8')
        request = Request(self.base_url + path, data=data,
                          headers={'Content-Type': 'application/json'} if data else {})
        try:
            with self.opener.open(request, timeout=self.request_timeout) as response:
                return response.read()
        except HTTPError as error:
            detail = error.read().decode('utf-8', errors='replace')
            raise GenerationError(f'ComfyUI HTTP {error.code} at {path}:\n{detail}') from error
        except (URLError, TimeoutError) as error:
            raise GenerationError(f'Cannot reach ComfyUI at {self.base_url}{path}: {error}') from error

    def json(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        result = json.loads(self.request(path, payload))
        if not isinstance(result, dict):
            raise GenerationError(f'Expected a JSON object from {path}')
        return result


def load_json(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(result, dict):
        raise GenerationError(f'Expected a JSON object in {path}')
    return result


def catalog_icons(catalog: dict[str, Any], group: str, names: list[str] | None) -> list[tuple[str, str]]:
    icons: dict[str, str] = {}
    for section in ('abilities', 'resources'):
        subjects = catalog[section]
        if not isinstance(subjects, dict):
            raise GenerationError(f'Catalog {section} must be an object')
        for name, subject in subjects.items():
            if not re.fullmatch(r'[A-Za-z0-9_]+', name) or not isinstance(subject, str) or not subject.strip():
                raise GenerationError(f'Invalid catalog entry: {name!r}')
            if name in icons:
                raise GenerationError(f'Duplicate icon key: {name}')
            if group in {'all', section}:
                suffix = catalog['resource_style_suffix' if section == 'resources' else 'style_suffix']
                icons[name] = catalog['style_prefix'] + subject + suffix
    if names:
        unknown = set(names) - icons.keys()
        if unknown:
            raise GenerationError(f'Unknown icons in selected group: {", ".join(sorted(unknown))}')
        icons = {name: icons[name] for name in dict.fromkeys(names)}
    if not icons:
        raise GenerationError('No icons selected')
    return list(icons.items())


def icon_seed(base_seed: int, name: str) -> int:
    offset = int.from_bytes(hashlib.sha256(name.encode('utf-8')).digest()[:8], 'big')
    return (base_seed + offset) % (2 ** 64)


def api_graph(workflow: dict[str, Any], name: str, text: str, seed: int) -> dict[str, Any]:
    """Convert this repository's UI workflow, including its widget values, to API format."""
    links = {link[0]: link for link in workflow['links']}
    graph: dict[str, Any] = {}
    for node in workflow['nodes']:
        kind = node['type']
        if kind not in WIDGETS or node.get('mode', 0) != 0:
            raise GenerationError(f'Unsupported or disabled workflow node: {kind}')
        widgets = node.get('widgets_values', [])
        if len(widgets) != len(WIDGETS[kind]):
            raise GenerationError(f'Unexpected widget layout for {kind}')
        inputs = {key: value for key, value in zip(WIDGETS[kind], widgets) if key is not None}
        for socket in node.get('inputs', []):
            link = links[socket['link']]
            inputs[socket['name']] = [str(link[1]), link[2]]
        graph[str(node['id'])] = {'class_type': kind, 'inputs': inputs}
    for node_id, kind in {'4': 'CLIPTextEncode', '8': 'KSampler', **{key: 'SaveImage' for key in SAVES}}.items():
        if graph.get(node_id, {}).get('class_type') != kind:
            raise GenerationError(f'Workflow node {node_id} must be {kind}')
    graph['4']['inputs']['text'] = text
    graph['8']['inputs']['seed'] = seed
    for node_id, (folder, _) in SAVES.items():
        graph[node_id]['inputs']['filename_prefix'] = f'Gunslinger/{folder}/{name}'
    return graph


def preflight(graph: dict[str, Any], schemas: dict[str, Any]) -> None:
    for node in graph.values():
        kind, inputs = node['class_type'], node['inputs']
        if kind not in schemas:
            raise GenerationError(f'ComfyUI is missing node {kind}')
        schema = schemas[kind]['input']
        fields = {**schema.get('required', {}), **schema.get('optional', {})}
        for required in schema.get('required', {}):
            if required not in inputs:
                raise GenerationError(f'Missing required input {kind}.{required}')
        for key, value in inputs.items():
            if key not in fields:
                raise GenerationError(f'Unknown input {kind}.{key}')
            if isinstance(value, list):
                continue
            definition = fields[key]
            options = definition[0] if isinstance(definition[0], list) else (
                definition[1].get('options') if len(definition) > 1 and isinstance(definition[1], dict) else None)
            if options is not None and value not in options:
                hint = ' Install BiRefNet and restart ComfyUI; see To-do.md.' if kind == 'LoadBackgroundRemovalModel' else ''
                raise GenerationError(f'{kind}.{key}: {value!r} is unavailable; choices: {options}.{hint}')


def wait_for_result(client: ComfyClient, prompt_id: str, timeout: float, poll_interval: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while True:
        entry = client.json(f'/history/{prompt_id}').get(prompt_id)
        if entry:
            status = entry.get('status', {})
            messages = status.get('messages', [])
            if status.get('status_str') == 'error' or any(
                    message[0] in {'execution_error', 'execution_interrupted'} for message in messages):
                raise GenerationError(f'Generation failed for prompt {prompt_id}:\n{json.dumps(status, indent=2)}')
            if status.get('completed') and status.get('status_str') == 'success':
                return entry
        if time.monotonic() >= deadline:
            raise GenerationError(f'Timed out waiting for prompt {prompt_id}. It may still be queued/running; '
                                  'inspect ComfyUI before retrying. No shared queue was cancelled.')
        time.sleep(min(poll_interval, max(0, deadline - time.monotonic())))


def validate_png(data: bytes, size: int) -> None:
    if (len(data) < 33 or data[:8] != b'\x89PNG\r\n\x1a\n'
            or data[12:16] != b'IHDR' or struct.unpack_from('>II', data, 16) != (size, size)
            or data[25] != 6):
        raise GenerationError(f'Expected a {size}x{size} RGBA PNG from ComfyUI')


def download_outputs(client: ComfyClient, history: dict[str, Any], directory: Path,
                     name: str, overwrite: bool) -> list[Path]:
    downloaded: list[tuple[Path, bytes]] = []
    for node_id, (folder, size) in SAVES.items():
        images = history.get('outputs', {}).get(node_id, {}).get('images', [])
        if len(images) != 1:
            raise GenerationError(f'Expected exactly one image from SaveImage node {node_id}, got {len(images)}')
        image = images[0]
        query = urlencode({key: image[key] for key in ('filename', 'subfolder', 'type')})
        data = client.request('/view?' + query)
        validate_png(data, size)
        target = directory / folder / f'{name}.png'
        if target.exists() and not overwrite:
            raise GenerationError(f'Output already exists: {target}; use --overwrite or another --output')
        downloaded.append((target, data))
    for target, data in downloaded:
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix('.png.part')
        temp.write_bytes(data)
        temp.replace(target)
    return [target for target, _ in downloaded]


def positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('Must be a finite positive number')
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8188', help='Local ComfyUI API')
    parser.add_argument('--catalog', type=Path, default=HERE / 'icon_prompts.json')
    parser.add_argument('--workflow', type=Path, default=HERE / 'Gunslinger_Icons_FLUX.json')
    parser.add_argument('--output', type=Path, default=HERE / 'generated')
    parser.add_argument('--group', choices=('all', 'abilities', 'resources'), default='all')
    parser.add_argument('--icons', nargs='+', help='Exact catalog keys; otherwise generate the selected group')
    parser.add_argument('--seed', type=int, default=872341001, help='Base seed; each key gets a stable derived seed')
    parser.add_argument('--timeout', type=positive_float, default=1800, help='Seconds per icon, including queue wait')
    parser.add_argument('--poll-interval', type=positive_float, default=2)
    parser.add_argument('--overwrite', action='store_true', help='Replace selected local PNGs and metadata')
    parser.add_argument('--dry-run', action='store_true', help='Check live nodes/models and show plan without queueing')
    parser.add_argument('--list', action='store_true', help='List selected keys without contacting ComfyUI')
    args = parser.parse_args(argv)
    try:
        if not 0 <= args.seed < 2 ** 64:
            raise GenerationError('--seed must be between 0 and 18446744073709551615')
        selected = catalog_icons(load_json(args.catalog), args.group, args.icons)
        if args.list:
            print('\n'.join(name for name, _ in selected))
            return 0
        workflow = load_json(args.workflow)
        plans = [(name, text, api_graph(workflow, name, text, icon_seed(args.seed, name))) for name, text in selected]
        client = ComfyClient(args.url)
        schemas = client.json('/object_info')
        for name, _, graph in plans:
            preflight(graph, schemas)
            if not args.dry_run and not args.overwrite:
                targets = [args.output / folder / f'{name}.png' for folder, _ in SAVES.values()]
                targets.append(args.output / 'metadata' / f'{name}.json')
                for target in targets:
                    if target.exists():
                        raise GenerationError(f'Output already exists: {target}; use --overwrite or another --output')
        client_id = str(uuid.uuid4())
        for index, (name, text, graph) in enumerate(plans, 1):
            seed = graph['8']['inputs']['seed']
            print(f'[{index}/{len(plans)}] {name} seed={seed}', flush=True)
            if args.dry_run:
                continue
            response = client.json('/prompt', {'prompt': graph, 'client_id': client_id})
            if response.get('error') or response.get('node_errors') or not response.get('prompt_id'):
                raise GenerationError(f'ComfyUI rejected {name}:\n{json.dumps(response, indent=2)}')
            prompt_id = response['prompt_id']
            print(f'  Queued prompt {prompt_id}', flush=True)
            metadata_path = args.output / 'metadata' / f'{name}.json'
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata = {'icon': name, 'seed': seed, 'text': text, 'prompt_id': prompt_id,
                        'state': 'queued', 'api_prompt': graph}
            metadata_path.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
            history = wait_for_result(client, prompt_id, args.timeout, args.poll_interval)
            paths = download_outputs(client, history, args.output, name, args.overwrite)
            metadata.update(state='completed', files=[str(path.resolve()) for path in paths])
            metadata_path.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
            print(f'  Saved {len(paths)} RGBA PNGs to {args.output.resolve()}', flush=True)
        print('Dry run passed; nothing queued or written.' if args.dry_run else 'All selected icons completed.')
        return 0
    except (GenerationError, OSError, ValueError, KeyError, TypeError, IndexError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('Interrupted. Any submitted prompt may still run in ComfyUI; no shared queue was cancelled.', file=sys.stderr)
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
