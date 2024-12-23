from setuptools import setup, find_packages

setup(
    name="friday-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.75.1",
        "sqlalchemy>=1.4.35",
        "uvicorn[standard]>=0.17.6",
        "python-dotenv>=0.20.0",
        "strawberry-graphql[fastapi]>=0.114.0",
        "jsonschema>=4.21.1",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.3",
        "mysqlclient",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "pytest-asyncio>=0.14.0",
        "httpx>=0.24.0",
    ],
)
