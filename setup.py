from setuptools import setup

setup(
    name='django-edit-suggestion',
    version='1.34',
    description='A django package for creating multiple users editable models',
    url='https://github.com/smileservices/django-edit-suggestion',
    author='Vladimir Gorea',
    author_email='vladimir.gorea@gmail.com',
    license='MIT',
    packages=['django_edit_suggestion'],
    install_requires=[], # packages listed here will be automatically installed

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
    ],
)