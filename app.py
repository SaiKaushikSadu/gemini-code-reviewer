import os
from google import genai
from github import Github

def get_pr_diff(repo_name, pr_number, github_token):
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    return pr.get_files(), pr

def generate_review(client, diff_text):
    prompt = f"""
    You are a Principal Software Engineer. Review this code changes (diff) in a Pull Request.
    
    ## Instructions:
    1. Focus on bugs, security, and performance.
    2. Be concise. If it looks good, just say "✅ LGTM".
    3. Format with Markdown.

    ## Code Diff:
    {diff_text}
    """
    
    # NEW SYNTAX: Uses client.models.generate_content
    response = client.models.generate_content(
        model="gemini-2.5-pro", # You can switch to "gemini-2.5-flash" for speed
        contents=prompt
    )
    return response.text

def main():
    # 1. Setup Environment
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = int(os.getenv("PR_NUMBER"))

    # 2. Initialize Clients
    # The new SDK automatically looks for GEMINI_API_KEY in env if not passed,
    # but passing it explicitly is safe.
    client = genai.Client(api_key=gemini_key) 
    
    print(f"Reviewing PR #{pr_number} in {repo_name}...")

    # 3. Get Diff
    files, pr = get_pr_diff(repo_name, pr_number, github_token)
    full_diff = ""
    for file in files:
        full_diff += f"\n--- File: {file.filename} ---\n"
        full_diff += file.patch if file.patch else "Binary file/No changes."

    # 4. Generate & Post Review
    review_comment = generate_review(client, full_diff)
    
    pr.create_issue_comment(f"## 🤖 AI Code Review (Gemini 2.5 Pro)\n\n{review_comment}")
    print("Review posted!")

if __name__ == "__main__":
    main()