import os
import google.generativeai as genai
from github import Github

# 1. Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
# Using Gemini 2.5 Pro as requested
model = genai.GenerativeModel("gemini-2.5-pro") 

def get_pr_diff(repo_name, pr_number):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    # Get the diff (files changed)
    return pr.get_files(), pr

def generate_review(diff_text):
    prompt = f"""
    You are a Senior Software Engineer acting as a code reviewer.
    Analyze the following code changes (diff) for:
    1. Bugs or potential runtime errors.
    2. Security vulnerabilities.
    3. Code style and best practices (clean code).
    4. Performance improvements.
    
    If the code looks good, just say "LGTM".
    Format your response in Markdown.
    
    Code Diff:
    {diff_text}
    """
    response = model.generate_content(prompt)
    return response.text

def main():
    # Get context from GitHub Actions environment variables
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = int(os.getenv("PR_NUMBER"))
    
    print(f"Reviewing PR #{pr_number} in {repo_name}...")
    
    files, pr = get_pr_diff(repo_name, pr_number)
    
    # distinct_files ensures we don't send too much noise, 
    # but for 2.5 Pro's large context, we can often send the whole patch.
    full_diff = ""
    for file in files:
        full_diff += f"\n--- File: {file.filename} ---\n"
        full_diff += file.patch if file.patch else "Binary file or no changes shown."
    
    # Generate Review
    review_comment = generate_review(full_diff)
    
    # Post Comment to GitHub
    pr.create_issue_comment(f"## 🤖 AI Code Review (Gemini 2.5 Pro)\n\n{review_comment}")
    print("Review posted!")

if __name__ == "__main__":
    main()