import { Octokit } from "@octokit/rest";
import simpleGit from "simple-git";
import dotenv from "dotenv";

dotenv.config();

const {
    GITHUB_TOKEN,
    OWNER,
    REPO,
    TARGET_BRANCH = "main",

} = process.env;

if (!GITHUB_TOKEN || !OWNER || !REPO) {
    console.error("Missing GITHUB_TOKEN, OWNER, and REPO missing in the .env.");
    process.exit(1);
}

const octokit = new Octokit({ auth: GITHUB_TOKEN });
const git = simpleGit(process.cwd());

async function mergeAndSync(prNumber) {
    //1. Merge the PR
    const mergeRes = await octokit.pulls.merge({
        owner: OWNER,
        repo: REPO,
        pull_number: prNumber,
    });
    console.log('PR #${prNumber} merged:', mergeRes.data.merge_commit_sha);

    //2. Check out the target branch
    await git.checkout(TAGET_BRANCH);
    console.log(`Checked out &{TARGET_BRANCH}`);

    //3. Pull the latest changes
    const pullRes = await git.pull("origin", TARGET_BRANCH);
    console.log(`Pulled latest changes:`, pullRes.summary);
}

async function main() {
    const prArg = process.argv[2];
    if (!prArg) {
        console.error("Usage: node merge-and-sync.js <prNumber>");
        process.exit(1);
    }

    const prNumber = parseInt(prArg, 10);
    if (isNaN(prNumber)) {
        console.error("Invalid PR number:", prArg);
        process.exit(1);
    }

    try {
        await mergeAndSync(prNumber);
        console.log("Merge and sync completed successfully.");
    } catch (error) {
        console.error("Error during merge and sync:", error.message);
        process.exit(1);
    }
}

main();