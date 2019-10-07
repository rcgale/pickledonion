import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='pickledonion',
    version='0.1.0',
    author='Robert Gale',
    author_email='rcgale@gmail.com',
    packages=['pickledonion'],
    url='https://github.com/rcgale/pickledonion',
    description='Python pickle disk caching which encourages configuration on the outer layers of an "onion" architecture',
    install_requires=[],
)

