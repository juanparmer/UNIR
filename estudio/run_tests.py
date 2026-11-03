"""Ejecuta pruebas aisladas y guarda un log con fecha y resultado reales."""
import argparse
import io
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            stream.write(text)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'evidencias')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    output = Tee(sys.stdout, buffer)
    output.write(f'Ejecución UTC: {datetime.now(timezone.utc).isoformat()}\n')
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_*.py')
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    (args.output / 'pruebas.log').write_text(buffer.getvalue(), encoding='utf-8')
    summary = {'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'tests': result.testsRun,
               'failures': len(result.failures), 'errors': len(result.errors),
               'skipped': len(result.skipped), 'success': result.wasSuccessful()}
    (args.output / 'resultado.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
