from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
from threading import Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from unittest.mock import patch
import zlib


ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'artwork' / 'comfyui'
SPEC = importlib.util.spec_from_file_location('generate_icons', HERE / 'generate_icons.py')
assert SPEC is not None and SPEC.loader is not None
icons = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(icons)


def png(size: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    header = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
    rows = (b'\0' + b'\xff\x80\0\xff' * size) * size
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')


class FakeComfyHandler(BaseHTTPRequestHandler):
    submissions: list[dict] = []
    schemas: dict = {}

    def log_message(self, format: str, *args: object) -> None:
        pass

    def reply(self, data: bytes, content_type: str = 'application/json') -> None:
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == '/object_info':
            self.reply(json.dumps(self.schemas).encode())
        elif self.path.startswith('/history/'):
            outputs = {node_id: {'images': [{'filename': f'{size}.png', 'subfolder': '', 'type': 'output'}]}
                       for node_id, (_, size) in icons.SAVES.items()}
            self.reply(json.dumps({'test-prompt': {'status': {'completed': True, 'status_str': 'success'},
                                                 'outputs': outputs}}).encode())
        elif self.path.startswith('/view?'):
            from urllib.parse import parse_qs, urlsplit
            size = int(parse_qs(urlsplit(self.path).query)['filename'][0].split('.')[0])
            self.reply(png(size), 'image/png')
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path != '/prompt':
            self.send_error(404)
            return
        length = int(self.headers['Content-Length'])
        self.submissions.append(json.loads(self.rfile.read(length)))
        self.reply(b'{"prompt_id":"test-prompt","node_errors":{}}')


class ComfyIconTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = icons.load_json(HERE / 'icon_prompts.json')
        self.workflow = icons.load_json(HERE / 'Gunslinger_Icons_FLUX.json')

    def graph(self, name: str = 'GSL_MercilessShot') -> dict:
        text = icons.catalog_icons(self.catalog, 'all', [name])[0][1]
        return icons.api_graph(self.workflow, name, text, icons.icon_seed(123, name))

    def test_catalog_coverage_selection_and_current_edits(self) -> None:
        self.assertEqual(len(icons.catalog_icons(self.catalog, 'all', None)), 91)
        self.assertEqual(len(icons.catalog_icons(self.catalog, 'resources', None)), 6)
        self.assertEqual([name for name, _ in icons.catalog_icons(self.catalog, 'classes', None)],
                         ['Gunslinger', 'Marksman', 'Desperado', 'ArcaneGunsman'])
        self.assertIn(self.catalog['class_style_suffix'], icons.catalog_icons(self.catalog, 'classes', None)[0][1])
        self.catalog['abilities']['GSL_MercilessShot'] = 'edited subject'
        text = icons.catalog_icons(self.catalog, 'abilities', ['GSL_MercilessShot'])[0][1]
        self.assertIn('edited subject', text)
        with self.assertRaises(icons.GenerationError):
            icons.catalog_icons(self.catalog, 'resources', ['GSL_MercilessShot'])

    def test_api_conversion_preserves_alpha_and_sampler_wiring(self) -> None:
        graph = self.graph()
        self.assertEqual(graph['8']['inputs']['cfg'], 1)
        self.assertNotIn('fixed', graph['8']['inputs'].values())
        self.assertEqual(graph['12']['inputs']['mask'], ['11', 0])
        self.assertEqual(graph['13']['inputs']['alpha'], ['12', 0])
        self.assertEqual(graph['2']['inputs']['clip_name2'], 't5xxl_fp8_e4m3fn_scaled.safetensors')
        for node_id, (folder, _) in icons.SAVES.items():
            self.assertEqual(graph[node_id]['inputs']['filename_prefix'], f'Gunslinger/{folder}/GSL_MercilessShot')
        self.assertEqual(icons.icon_seed(123, 'a'), icons.icon_seed(123, 'a'))
        self.assertNotEqual(icons.icon_seed(123, 'a'), icons.icon_seed(123, 'b'))

    def test_preflight_reports_empty_background_model_choices(self) -> None:
        graph = {'10': self.graph()['10']}
        schema = {'LoadBackgroundRemovalModel': {'input': {'required': {
            'bg_removal_name': ['COMBO', {'options': []}]}}}}
        with self.assertRaisesRegex(icons.GenerationError, 'Install BiRefNet'):
            icons.preflight(graph, schema)

    def test_history_errors_and_timeout_are_explicit(self) -> None:
        client = icons.ComfyClient('http://127.0.0.1:8188')
        for status in ({'completed': False, 'status_str': 'error'},
                       {'messages': [['execution_interrupted', {}]]}):
            with patch.object(client, 'json', return_value={'p': {'status': status}}):
                with self.assertRaisesRegex(icons.GenerationError, 'Generation failed'):
                    icons.wait_for_result(client, 'p', 1, .01)
        with patch.object(client, 'json', return_value={}):
            with self.assertRaisesRegex(icons.GenerationError, 'may still be queued'):
                icons.wait_for_result(client, 'p', .001, .001)

    def test_png_dimensions_and_alpha_are_required(self) -> None:
        icons.validate_png(png(48), 48)
        with self.assertRaises(icons.GenerationError):
            icons.validate_png(png(64), 48)
        wrong_alpha = bytearray(png(48))
        wrong_alpha[25] = 2
        with self.assertRaises(icons.GenerationError):
            icons.validate_png(bytes(wrong_alpha), 48)

    def test_external_api_urls_are_rejected(self) -> None:
        for url in ('https://example.com', 'http://192.168.1.2:8188', 'http://localhost:8188/redirect'):
            with self.assertRaises(icons.GenerationError):
                icons.ComfyClient(url)

    def test_http_generation_dry_run_and_overwrite_protection(self) -> None:
        graph = self.graph()
        FakeComfyHandler.submissions = []
        FakeComfyHandler.schemas = {
            node['class_type']: {'input': {'required': {key: ['STRING'] for key in node['inputs']}}}
            for node in graph.values()
        }
        server = ThreadingHTTPServer(('127.0.0.1', 0), FakeComfyHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with TemporaryDirectory() as folder, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                args = ['--url', f'http://127.0.0.1:{server.server_port}', '--output', folder,
                        '--icons', 'GSL_MercilessShot']
                self.assertEqual(icons.main([*args, '--dry-run']), 0)
                self.assertEqual(FakeComfyHandler.submissions, [])
                self.assertEqual(list(Path(folder).iterdir()), [])
                self.assertEqual(icons.main(args), 0)
                self.assertEqual(len(FakeComfyHandler.submissions), 1)
                for subfolder, size in icons.SAVES.values():
                    icons.validate_png((Path(folder) / subfolder / 'GSL_MercilessShot.png').read_bytes(), size)
                metadata = icons.load_json(Path(folder) / 'metadata' / 'GSL_MercilessShot.json')
                self.assertEqual(metadata['state'], 'completed')
                self.assertEqual(metadata['prompt_id'], 'test-prompt')
                self.assertEqual(icons.main(args), 1)
                self.assertEqual(len(FakeComfyHandler.submissions), 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
