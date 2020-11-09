from setuptools import setup

setup(
    name='django-edit-suggestion',
    version='1.0',
    description='A django package for creating multiple users editable models',
    url='https://github.com/smileservices/django-simple-history',
    author='Vladimir Gorea',
    author_email='vladimir.gorea@gmail.com',
    license='MIT',
    packages=['django-edit-suggestion'],
    install_requires=[], # packages listed here will be automatically installed

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: > 3',
    ],
)