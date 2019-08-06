import importlib
import os
import subprocess
import sys
from pathlib import Path
from shutil import copytree, make_archive
from tempfile import TemporaryDirectory

from ...utils.exceptions import KnownError

server_main_py = '''# Auto-generated by Polecat

from polecat.deploy.aws.server import LambdaServer

server = LambdaServer()


def handler(event, context):
    return server.handle(event, context)
'''


def build(project, source=None, local_packages=None, feedback=None):
    feedback.declare_steps(
        'Install polecat', 'Install dependencies', 'Create archive'
    )
    source = Path(source) if source else (Path.cwd() / project)
    local_packages = local_packages or []
    with TemporaryDirectory() as root:
        root = Path(root)
        if not source.exists():
            # TODO: Don't like this known error stuff.
            raise KnownError('source path does not exist')
        with feedback('Install polecat') as fb:
            # TODO: Find a way to automatically set this version.
            # install_package('polecat==0.0.5', Path(root))
            for pkg in find_polecat_package(fb):
                install_package(pkg, Path(root))
        with feedback('Install dependencies') as fb:
            for lpkg in local_packages:
                for pkg in find_package(lpkg, fb):
                    install_package(pkg, Path(root))
        with feedback('Create archive') as fb:
            copytree(source, root / os.path.basename(source))
            with open(root / 'main.py', 'wt') as f:
                f.write(server_main_py)
            make_archive('server', 'zip', str(root))


def install_package(package, root):
    subprocess.check_output([
        sys.executable, '-m', 'pip', 'install', '--target', root, package
    ], stderr=subprocess.PIPE)


def find_polecat_package(feedback):
    try:
        import polecat
    except ImportError:
        return ('polecat',)
    root = Path(polecat.__file__).parent.parent
    setup_file = root / 'setup.py'
    if setup_file.is_file():
        feedback.add_notice('Using local package polecat')
        # TODO: So long as the current pip version of graphql-server does not
        # use graphql-core-next we need to manually install it.
        return (root, 'https://github.com/norman-thomas/graphql-server-core/tarball/master')
    else:
        return ('polecat',)


def find_package(package, feedback):
    try:
        module = importlib.import_module(package)
    except ImportError:
        return (package,)
    root = Path(module.__file__).parent.parent
    setup_file = root / 'setup.py'
    if setup_file.is_file():
        feedback.add_notice(f'Using local package {package}')
        return (root,)
    else:
        return (package,)
