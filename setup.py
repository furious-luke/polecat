from setuptools import find_packages, setup

version = '0.0.9'

setup(
    name='polecat',
    version=version,
    author='Luke Hodkinson',
    author_email='furious.luke@gmail.com',
    maintainer='Luke Hodkinson',
    maintainer_email='furious.luke@gmail.com',
    description='',
    long_description='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License'
    ],
    packages=find_packages(exclude=['tests', 'extern']),
    include_package_data=True,
    package_data={'': ['*.txt', '*.js', '*.html', '*.*']},
    install_requires=[
        'ujson==1.35',
        'psycopg2-binary==2.8.4',
        'graphql-core-next==1.0.2',
        # TODO: This should be in "cli".
        'polecat-feedback==0.0.0',
        # 'graphql-server-core @ https://github.com/norman-thomas/graphql-server-core/tarball/master',
        'pyjwt==1.7.1',
        'pytimeparse==1.1.8',
        'pytz==2019.1',
        # Used to be in extras...
        'click==7.0',
        'halo==0.0.23',
        'termcolor==1.1.0',
        'cached-property==1.5.1'
    ],
    extras_require={
        'cli': [
            'pytest==4.3.1',
            'pytest-asyncio==0.10.0',
            'pytest-polecat==0.0.0',
            'factory-boy==2.11.1',
            'sanic==19.3.1',
            'boto3==1.9.125',
            'coolname==1.1.0',
            'python-Levenshtein==0.12.0'
        ]
    },
    entry_points={
        'console_scripts': [
            'polecat=polecat.cli.entrypoint:entrypoint'
        ]
    },
    zip_safe=True
)
