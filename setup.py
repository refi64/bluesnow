from setuptools import setup


with open('README.rst') as fp:
    readme = fp.read()

with open('requirements.txt') as fp:
    requirements = fp.read().splitlines()


setup(
    name='bluesnow',
    version='0.1.1',
    description='Package your Python applications into a single script',
    long_description=readme,
    author='Ryan Gonzalez',
    author_email='rymg19@gmail.com',
    license='BSD',
    url='https://github.com/kirbyfan64/bluesnow',
    py_modules=['bluesnow'],
    entry_points={
        'console_scripts': ['bluesnow = bluesnow:main']
    },
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: BSD License',
    ],
)
