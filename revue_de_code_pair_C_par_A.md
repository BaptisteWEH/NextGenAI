Code Review - Branch Pair_C

This review is based on the structure and metadata of the NextGenAI-Pair_C.zip archive.

1. Architecture and Repository Structure

The architecture is generally oriented towards a learning or assessment environment (TDs/labs, lectures, assessments).

Strengths

Logical organization: The separation between kit-td1, lectures, reports, and templates is clear.

Abundant documentation: The presence of numerous instruction and report files (.md, .html, .pdf) is excellent for an educational context.

Structured data: Data (SQLite, CSV files) is well-contained within kit-td1/data/.

Points of Attention and Improvements

Format redundancy: Many documents (e.g., enonce-td1-en, syllabus-en) exist in three formats (Markdown, HTML, PDF). It is recommended to version only the Markdown files and generate the PDFs/HTMLs automatically via CI/CD (like GitHub Actions).

Naming and hierarchy of kit-td1: The kit-td1 folder surprisingly contains subfolders TD1, TD2, and TD3. It should be renamed to something like labs or tds to be consistent with its actual content.

Cluttered root directory: Files like assessment-en.*, before-td1-en.*, and submission-en.* could be grouped in a docs/ or course_info/ folder to clean up the root.

2. Python Code and Best Practices

The repository contains several Python scripts, mostly in the lab spaces.

Items to check (Static analysis recommended)

Modularity: The script skeleton-multi-llm-en.py is very large (~41 KB). It should probably be divided into smaller modules (e.g., API calls, data processing).

Dependency management: The requirements.txt file is only 17 bytes. This is abnormally small for a project using LLMs and SQLite. Critical dependencies (e.g., openai, pandas, etc.) are highly likely missing.

SQL Security: sandbox_sqlite.py interacts with boutique.sqlite. Verify that there is no risk of SQL injection, especially if LLMs generate queries that are executed automatically.

API Key Security: Ensure that no API keys are hardcoded in the scripts, particularly in skeleton-multi-llm-en.py, and that a .env file is properly used (and listed in .gitignore).

3. Data and Trace Files

Strengths

Trace preservation: Saving execution logs (traces-A.csv, state-X.jsonl) is very useful for analyzing and comparing AI model behavior.

Points of Attention

Volume and Git History: Generated files (traces-td1.jsonl at 115 KB, multiple CSVs) risk bloating the Git history if students rerun the scripts frequently. It is often better to add them to .gitignore and only version reference datasets.

.gitignore Check: Ensure it correctly excludes virtual environments (venv/, .venv/), caches (__pycache__/), and environment variable files (.env).

Recommended Action Plan

Restructure folders: Rename kit-td1 and clean up the root directory.

Review requirements.txt: Generate a complete file using pip freeze > requirements.txt or use a package manager like poetry.

Implement a robust .gitignore: Exclude non-essential, large execution logs.

Refactor code: Break down skeleton-multi-llm-en.py for better maintainability.
