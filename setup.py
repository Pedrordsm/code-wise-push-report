from setuptools import setup, find_packages 
try:
    with open('requirements.txt', encoding='utf-8') as f:
        required = f.read().splitlines()
except FileNotFoundError:
    required = []

setup(
    name="codewise_lib",
    version="3.1.8",
    author="BPC",
    description="análise de código e automação de PRs com CrewAI.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",

    packages=find_packages(),

    package_data={
        'codewise_lib': ['config/*.yaml'],
    },
    include_package_data=True,
    install_requires=required,
    python_requires='>=3.11',
    entry_points={
        'console_scripts': [
            'codewise-pr=scripts.codewise_review_win:main_pr_interactive', 
            'codewise-pr-origin=scripts.codewise_review_win:main_pr_origin',   
            'codewise-pr-upstream=scripts.codewise_review_win:main_pr_upstream', 
            'codewise-lint=scripts.codewise_review_win:main_lint',
            'codewise-init=scripts.install_hook:main',
            'codewise-help=scripts.help:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators"
    ],
)