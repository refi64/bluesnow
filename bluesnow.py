try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

try:
    from os import scandir
except ImportError:
    from scandir import scandir

from pkg_resources import EntryPoint
from setuptools import Command
from tqdm import tqdm

import io
import lzma
import os
import pip
import tempfile
import sys


TEMPLATE = '''#!/usr/bin/env python3
import importlib.abc
import lzma
import sys

class Loader(importlib.abc.SourceLoader):
    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.source = data.decode('utf-8')

    def exec_module(self, module):
        module.__file__ = self.name
        super(Loader, self).exec_module(module)

    def get_filename(self, fullname):
        return self.name

    def get_data(self, path):
        return self.data


class Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        try:
            is_package, contents = DATA[name]
        except KeyError:
            return None

        if DATA_COMPRESSED:
            contents = lzma.decompress(contents)

        return importlib.machinery.ModuleSpec(name, Loader(name, contents),
                                              is_package=is_package)

# These are replaced by BlueSnow.write_output_file

{{DATA}}

sys.meta_path.insert(0, Finder())

if __name__ == '__main__':
{{MAIN}}
'''


class BlueSnow:
    def __init__(self, output, compress):
        self.output = Path(output)
        self.compress = compress

    def install_deps(self, package_dir, pip_args):
        pip.main(['install', '-t', package_dir, '.'] + pip_args)

    def get_package_files(self, path, root=None):
        if root is None:
            root = path

        for entry in scandir(str(path)):
            if entry.is_dir():
                if entry.name != '__pycache__' and not entry.name.endswith('.dist-info'):
                    yield from self.get_package_files(entry.path, root)
            elif entry.is_file():
                yield Path(entry.path), Path(entry.path).relative_to(root)

    def incremental_read(self, fp, size=4096):
        while True:
            data = fp.read(size)
            if not data:
                break
            yield data

    def write_data(self, package_dir, out):
        files = self.get_package_files(package_dir)
        progress = tqdm(files, desc=' '*50)
        for path, shortpath in progress:
            if self.compress:
                lzc = lzma.LZMACompressor()

            if shortpath.name == '__init__.py':
                module_path = shortpath.parent
            elif shortpath.suffix == '.py':
                module_path = shortpath.with_suffix('')
            else:
                continue

            progress.set_description('{: <50}'.format(str(shortpath)))
            with path.open('rb') as fp:
                out.write(repr(str(module_path).replace('/', '.')))
                out.write(':(')
                out.write(str(shortpath.name == '__init__.py'))
                out.write(',')

                for part in self.incremental_read(fp):
                    if self.compress:
                        part = lzc.compress(part)
                        if not part:
                            continue
                    out.write(repr(part))
                    out.write('\\\n')

                if self.compress:
                    out.write(repr(lzc.flush()))
                else:
                    out.write('b""')
                out.write('),')

    def write_output_file(self, package_dir, entry_point):
        output = (self.output / entry_point.name).with_suffix('.py')

        with output.open('w') as out:
            for line in TEMPLATE.split('\n'):
                if line == '{{DATA}}':
                    out.write('DATA = {')
                    out.flush()
                    self.write_data(package_dir, out)
                    out.write('}\n')

                    out.write('DATA_COMPRESSED = ')
                    out.write(str(self.compress))

                elif line == '{{MAIN}}':
                    module = entry_point.module_name
                    func = '.'.join(entry_point.attrs)
                    out.write('    import {} as m; m.{}()'.format(module, func))

                else:
                    out.write(line)
                    out.write('\n')
                out.flush()

        output.chmod(0o775)

    def process(self, pip_args, entry_points):
        self.output.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as package_dir:
            self.install_deps(package_dir, pip_args)
            for entry_point in entry_points.values():
                self.write_output_file(package_dir, entry_point)


class BlueSnowCommand(Command):
    description = 'Compile the entry points using BlueSnow.'

    user_options = [
        ('output=', 'o', 'The output directory'),
        ('compress', 'c', 'Compress the data'),
    ]

    boolean_options = ['compress']

    def initialize_options(self):
        self.output = 'bluesnow-out'
        self.compress = False

    def finalize_options(self):
        pass

    def run(self):
        requires = self.distribution.install_requires
        ep = {}
        for section, items in self.distribution.entry_points.items():
            ep.update(EntryPoint.parse_group(section, items))

        BlueSnow(self.output, self.compress).process(requires, ep)


setuptools_cmdclass = { 'bluesnow': BlueSnowCommand }


def driver(source: ('The Python package/directory containing the entry points',
                    'option') = '.',
           output: ('The output directory', 'option') = 'bluesnow-out',
           compress: ('Compress the data', 'flag') = False,
           *entry_points: 'The list of entry points'):
    if not entry_points:
        sys.exit('One or more entry points are required.')

    ep = EntryPoint.parse_group('entry_points', entry_points)
    BlueSnow(output, compress).process([source], ep)


def main():
    import plac
    plac.call(driver)


if __name__ == '__main__':
    main()
