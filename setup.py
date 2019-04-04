import os

from setuptools import find_packages, setup

version = '0.0.5'

setup(
    name='polecat',
    version=version,
    author='Luke Hodkinson',
    author_email='furious.luke@gmail.com',
    maintainer='Luke Hodkinson',
    maintainer_email='furious.luke@gmail.com',
    description='',
    long_description=open(
        os.path.join(os.path.dirname(__file__), 'README.md')
    ).read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License'
    ],
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    package_data={'': ['*.txt', '*.js', '*.html', '*.*']},
    install_requires=[
        'ujson==1.35',
        'psycopg2-binary==2.7.7',
        'graphql-core-next==1.0.2',
        'graphql-server-core @ https://github.com/norman-thomas/graphql-server-core/tarball/master',
        'pyjwt==1.7.1'
    ],
    dependency_links=[
        # 'git+https://github.com/norman-thomas/graphql-server-core#egg=graphql_server'
    ],
    entry_points={
        'console_scripts': [
            'polecat=polecat.cli.entrypoint:entrypoint'
        ]
    },
    zip_safe=False
)
