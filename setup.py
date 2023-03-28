"""Setuptools setup file"""

from setuptools import setup, find_packages

setup(
    name='crunch-slackbot',
    version='0.2',
    description="Various crunchbot (pmxbot) plugins built by Crunch.io",
    #long_description = get_description(),
    install_requires=[
        'pmxbot[slack,irc]',
        'requests',
        ],
    tests_require=[],
    extras_require={},
    author='Crunch.io',
    author_email='systems@crunch.io',
    license='MIT',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    namespace_packages=["slackbot"],
    include_package_data=True,
    entry_points={
        'pmxbot_handlers': ['slackbot-core = slackbot.core.handler',
                            'slackbot-pivotal = slackbot.pivotal',
			   ]
        },
    zip_safe=True,
    classifiers=[
        'Development Status :: 2 - Development',
        'Intended Audience :: IRC Bot (pmxbot) Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)

