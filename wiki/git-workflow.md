# `Git workflow` for tasks

> [!NOTE]
> This procedure is based on the [`GitHub flow`](./github.md#github-flow).

```text
Issue ➜ Branch ➜ Commits ➜ PR ➜ Review ➜ Merge
```

The following diagram shows this workflow in the context of repositories:

<img alt="Git workflow" src="./images/git-workflow/git-workflow.drawio.svg" style="width:100%"></img>

Outline:

- [Create a `Lab Task` issue](#create-a-lab-task-issue)
- [Switch to the `main` branch](#switch-to-the-main-branch)
- [Pull changes from `main` on `origin`](#pull-changes-from-main-on-origin)
- [Pull changes from `main` on `upstream`](#pull-changes-from-main-on-upstream)
- [Switch to the `<task-branch>`](#switch-to-the-task-branch)
  - [`<task-branch>`](#task-branch)
- [Edit files](#edit-files)
- [Commit changes](#commit-changes)
- [(Optional) Undo commits](#optional-undo-commits)
- [Push commits](#push-commits)
- [Create a PR to the `main` branch in your fork](#create-a-pr-to-the-main-branch-in-your-fork)
- [Get a PR review](#get-a-pr-review)
  - [PR review rules](#pr-review-rules)
    - [PR review rules for the reviewer](#pr-review-rules-for-the-reviewer)
    - [PR review rules for the author](#pr-review-rules-for-the-author)
- [Merge the PR](#merge-the-pr)
- [Clean up](#clean-up)

## Create a `Lab Task` issue

[Create an issue](./github.md#create-an-issue) using the `Lab Task` [issue form](./github.md#issue-form).

## Switch to the `main` branch

[Switch to the `main` branch](./git-vscode.md#switch-to-the-branch) in `VS Code`.

## Pull changes from `main` on `origin`

[Pull changes](./git-vscode.md#pull-changes-from-the-branch-on-remote) from `main` on [`origin`](./github.md#origin).

## Pull changes from `main` on `upstream`

[Pull changes](./git-vscode.md#pull-changes-from-the-branch-on-remote) from `main` on [`upstream`](./github.md#upstream) to get the latest fixes from the instructors' repository.

## Switch to the `<task-branch>`

[Create a new `<task-branch>` and switch to it](./git-vscode.md#switch-to-a-new-branch).

### `<task-branch>`

The [new branch for the task](#switch-to-the-task-branch).

Alternatively, the name of that branch (without `<` and `>`).

## Edit files

[Edit files](./vs-code.md#editor) using `VS Code` to produce changes.

## Commit changes

[Commit changes](./git-vscode.md#commit-changes) to the [`<task-branch>`](#task-branch) to complete the task.

## (Optional) Undo commits

[Undo commits](./git-vscode.md#undo-commits) if necessary.

## Push commits

1. [Publish the branch](./git-vscode.md#publish-the-branch) with your changes if it's not yet published.
2. [Push more commits](./git-vscode.md#push-more-commits) to the published branch if necessary.

## Create a PR to the `main` branch in your fork

Create a PR from [`<task-branch>`](#task-branch) to `main` **in your own fork** (not the upstream).

1. Go to your fork on `GitHub` and click `Pull requests` → `New pull request`.
2. **Change the base repository to your fork.** By default, `GitHub` sets the base to the upstream repo (`inno-se-toolkit/<lab-repo-name>`). Click `base repository` and select `<your-github-username>/<lab-repo-name>`.
3. Set the base branch to `main` and the compare branch to your [`<task-branch>`](#task-branch).
4. Write the PR title and description. Link the issue by writing `Closes #<issue-number>` in the description.
5. Click `Create pull request`.

> [!WARNING]
> Do **not** create PRs to the upstream `inno-se-toolkit` repo. Your PR must target `main` in **your fork**.

## Get a PR review

1. [Request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/requesting-a-pull-request-review#requesting-reviews-from-collaborators-and-organization-members) a review of the PR from the collaborator.

2. Conduct the PR review together following the [PR review rules](#pr-review-rules).

3. Get the collaborator to approve the PR.

### PR review rules

- [PR review rules for the reviewer](#pr-review-rules-for-the-reviewer)
- [PR review rules for the author](#pr-review-rules-for-the-author)

#### PR review rules for the reviewer

As a reviewer:

- Check the task's **Acceptance criteria**.
- Leave at least one [comment](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/commenting-on-a-pull-request#adding-comments-to-a-pull-request) — point out problems or confirm that items look good.
- [Approve](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/reviewing-proposed-changes-in-a-pull-request#submitting-your-review) the PR when all relevant acceptance criteria are met.

#### PR review rules for the author

As a PR author:

- Address reviewer comments (fix issues or explain your reasoning).
- Reply to comments, e.g., "Fixed in d0d5aeb".

## Merge the PR

Click `Merge pull request`.

## Clean up

1. Close the issue.

2. Delete the PR branch ([`<task-branch>`](#task-branch)).
