from polecat.cli.aws import *  # noqa
from polecat.cli.build import *  # noqa
from polecat.cli.deploy import *  # noqa
from polecat.cli.deployment import *  # noqa
from polecat.cli.example import *  # noqa
from polecat.cli.main import main
from polecat.cli.project import *  # noqa
from polecat.cli.publish import *  # noqa
from polecat.cli.secret import *  # noqa
from polecat.cli.server import *  # noqa
from polecat.cli.start import *  # noqa
from polecat.cli.test import *  # noqa
from polecat.cli.upload import *  # noqa


def entrypoint():
    main(auto_envvar_prefix='POLECAT', obj={})


if __name__ == '__main__':
    entrypoint()
