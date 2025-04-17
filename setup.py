from setuptools import setup, find_packages

setup(
    name="codereviewer",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "flask==3.0.2",
        "requests==2.31.0",
        "tenacity==8.2.3",
        "faiss-cpu==1.7.4",
        "numpy==1.26.4",
        "python-dotenv==1.0.1",
        "gunicorn==21.2.0",
        "sentence-transformers==2.2.2",
        "torch==2.2.1+cpu",
        "torchvision==0.17.1+cpu",
        "torchaudio==2.2.1+cpu"
    ],
    python_requires=">=3.8",
) 