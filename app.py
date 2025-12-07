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
    You are a Senior Software Engineer. Review the following code changes (diff) from a Pull Request.
    
    ## Instructions:
    1. Identify critical bugs, security flaws, and performance issues.
    2. Be concise. Avoid explaining what the code does; focus on *fixing* it.
    3. If the code is good, strictly output: "✅ **LGTM!** No critical issues found."
    4. Format your response in clear Markdown.

    ## Code Changes:
    {diff_text}
    """
    
    # Switched to Flash model to fix the Quota Error
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )
    return response.text

def main():
    # 1. Setup Environment
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = int(os.getenv("PR_NUMBER"))

    # 2. Initialize Client
    client = genai.Client(api_key=gemini_key)
    
    print(f"Reviewing PR #{pr_number} in {repo_name} using Gemini 2.5 Flash...")

    # 3. Get Diff
    files, pr = get_pr_diff(repo_name, pr_number, github_token)
    
    full_diff = ""
    for file in files:
        # Skip package-lock, yarn.lock, images, etc. to save tokens
        if file.filename.endswith(('.json', '.lock', '.png', '.jpg', '.svg')):
            continue
            
        full_diff += f"\n--- File: {file.filename} ---\n"
        full_diff += file.patch if file.patch else "No changes detected."

    # 4. Generate & Post Review
    if not full_diff:
        print("No reviewable files found.")
        return

    review_comment = generate_review(client, full_diff)
    
    pr.create_issue_comment(f"## ⚡ Gemini 2.5 Flash Review\n\n{review_comment}")
    print("Review posted successfully!")

if __name__ == "__main__":
    main()