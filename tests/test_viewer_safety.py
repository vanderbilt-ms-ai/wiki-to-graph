"""Untrusted prose stays data in both the offline file and Markdown renderer."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/wiki-to-graph/scripts/build_graph_viewer.py'


class ViewerSafety(unittest.TestCase):
    def test_cli_preserves_json_without_an_executable_script_breakout(self):
        graph = {'nodes': [{'id': 'a', 'type': 'concept', 'title': '</script><script>throw Error("injected")</script>'}], 'links': []}
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / 'graph.json', Path(directory) / 'viewer.html'
            source.write_text(json.dumps(graph), encoding='utf8')
            subprocess.run([sys.executable, str(SCRIPT), str(source), '-o', str(output)], check=True, capture_output=True)
            html = output.read_text(encoding='utf8')
            data = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S).group(1)
            self.assertEqual(json.loads(data), graph)
            self.assertNotIn('<script>throw Error', html)

    @unittest.skipUnless(shutil.which('node'), 'Node is optional; used here to execute the embedded renderer')
    def test_malformed_markdown_terminates_and_html_is_escaped(self):
        source = SCRIPT.read_text(encoding='utf8')
        renderer = source[source.index('function esc(t)'):source.index('// `related` and `contradicts`')]
        javascript = renderer + '\nconsole.log(JSON.stringify(renderMd("| malformed\\n<img src=x onerror=alert(1)>")));'
        result = subprocess.run(['node', '-e', javascript], capture_output=True, text=True, timeout=5, check=True)
        html = json.loads(result.stdout)
        self.assertIn('| malformed', html)
        self.assertIn('&lt;img', html)
        self.assertNotIn('<img', html)
