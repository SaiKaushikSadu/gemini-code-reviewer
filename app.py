import os
import sys  # <--- NEW: Needed to exit the script with an error
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
    3. IMPORTANT: At the very end of your review, you must output a final verdict.
       - If there are CRITICAL issues (bugs, security risks, breaking changes) that must be fixed, write: "VERDICT: REJECT"
       - If the code is safe to merge (even with minor nitpicks), write: "VERDICT: APPROVE"
    4. Format your response in clear Markdown.

    ## Code Changes:
    {diff_text}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )
    return response.text

def main():
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = int(os.getenv("PR_NUMBER"))

    client = genai.Client(api_key=gemini_key)
    
    print(f"Reviewing PR #{pr_number} in {repo_name}...")

    files, pr = get_pr_diff(repo_name, pr_number, github_token)
    
    full_diff = ""
    for file in files:
        if file.filename.endswith(('.json', '.lock', '.png', '.svg')):
            continue
        full_diff += f"\n--- File: {file.filename} ---\n"
        full_diff += file.patch if file.patch else "No changes detected."

    if not full_diff:
        print("No reviewable files found.")
        return

    review_comment = generate_review(client, full_diff)
    
    # Post the comment
    pr.create_issue_comment(f"## ⚡ Gemini 2.5 Flash Review\n\n{review_comment}")
    
    # Check for the Rejection Verdict
    if "VERDICT: REJECT" in review_comment:
        print("❌ Critical issues found. Blocking merge.")
        sys.exit(1)  # <--- This tells GitHub Actions the job FAILED
    else:
        print("✅ Review passed.")

if __name__ == "__main__":
    main()