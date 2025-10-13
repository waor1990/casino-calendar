#!/usr/bin/env node
/**
 * Remove stale npm staging directories inside node_modules on Windows.
 *
 * npm creates temporary directories that start with a leading dot and end with
 * a random hash (e.g. `.package-abc123`) while extracting packages. When the
 * install finishes these directories should be deleted, but on Windows file
 * locking can prevent npm from cleaning them up which causes a wave of
 * `npm warn cleanup` messages on the next install. This script proactively
 * removes any leftover staging folders so that npm install runs cleanly.
 */

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, "..", "..");
const NODE_MODULES_DIR = path.join(PROJECT_ROOT, "node_modules");

const PRESERVE_DIRS = new Set([
    ".bin",
    ".cache",
    ".parcel-cache",
    ".pnpm",
    ".pnpm-store",
    ".vite",
]);

const STALE_DIR_REGEX = /^\.[^\\/]+-[A-Za-z0-9]{4,}$/;
const MAX_RETRY_ATTEMPTS = 5;
const RETRY_DELAY_MS = 200;

function formatRelative(targetPath) {
    return path.relative(PROJECT_ROOT, targetPath) || ".";
}

async function findDirectoriesWithDots(startDir) {
    const queue = [startDir];
    const stalePaths = [];

    while (queue.length > 0) {
        const currentDir = queue.pop();
        let entries;

        try {
            entries = await fs.readdir(currentDir, { withFileTypes: true });
        } catch (error) {
            console.warn(
                `Skipping ${formatRelative(currentDir)}: unable to read directory (${error.code ?? error.message}).`,
            );
            continue;
        }

        for (const entry of entries) {
            const entryPath = path.join(currentDir, entry.name);

            if (entry.isSymbolicLink()) {
                continue;
            }

            if (entry.isDirectory()) {
                if (entry.name.startsWith(".")) {
                    if (PRESERVE_DIRS.has(entry.name)) {
                        continue;
                    }
                    if (STALE_DIR_REGEX.test(entry.name)) {
                        stalePaths.push(entryPath);
                        continue;
                    }
                }

                queue.push(entryPath);
            }
        }
    }

    return stalePaths;
}

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function ensureWritable(target) {
    let stats;

    try {
        stats = await fs.stat(target);
    } catch (error) {
        if (error.code === "ENOENT") {
            return;
        }
        throw error;
    }

    const desiredMode = stats.isDirectory() ? 0o777 : 0o666;

    if ((stats.mode & 0o222) === 0) {
        try {
            await fs.chmod(target, desiredMode);
        } catch (error) {
            if (error.code !== "ENOENT") {
                throw error;
            }
            return;
        }
    }

    if (!stats.isDirectory()) {
        return;
    }

    let entries;
    try {
        entries = await fs.readdir(target, { withFileTypes: true });
    } catch (error) {
        if (error.code === "ENOENT") {
            return;
        }
        throw error;
    }

    await Promise.all(
        entries
            .filter(entry => !entry.isSymbolicLink())
            .map(entry => ensureWritable(path.join(target, entry.name))),
    );
}

async function removeDirectories(directories) {
    const failures = [];

    directories.sort((a, b) => b.length - a.length);

    for (const directory of directories) {
        let attempt = 0;
        let lastError = null;

        while (attempt < MAX_RETRY_ATTEMPTS) {
            try {
                await fs.rm(directory, {
                    recursive: true,
                    force: true,
                    maxRetries: 0,
                });
                console.log(`  ✔ Removed ${formatRelative(directory)}`);
                lastError = null;
                break;
            } catch (error) {
                if (error.code === "ENOENT") {
                    console.log(`  ✔ Removed ${formatRelative(directory)}`);
                    lastError = null;
                    break;
                }

                lastError = error;
                attempt += 1;

                if (attempt >= MAX_RETRY_ATTEMPTS) {
                    break;
                }

                if (error.code === "EPERM" || error.code === "EACCES") {
                    try {
                        await ensureWritable(directory);
                    } catch (chmodError) {
                        // If we cannot adjust permissions, surface the original failure.
                        lastError = error;
                        break;
                    }
                }

                await sleep(RETRY_DELAY_MS * attempt);
            }
        }

        if (lastError) {
            const attemptCount = attempt;
            const attemptLabel = attemptCount === 1 ? "attempt" : "attempts";
            failures.push({ directory, error: lastError });
            console.warn(
                `  ✖ Failed to remove ${formatRelative(directory)} (${lastError.code ?? lastError.message}) after ${attemptCount} ${attemptLabel}`,
            );
        }
    }

    return failures;
}

async function main() {
    try {
        const stats = await fs.stat(NODE_MODULES_DIR);
        if (!stats.isDirectory()) {
            console.log("node_modules exists but is not a directory; skipping stale cleanup.");
            return;
        }
    } catch (error) {
        if (error.code === "ENOENT") {
            console.log("No node_modules directory found; skipping stale cleanup.");
            return;
        }
        throw error;
    }

    console.log("Scanning for stale npm staging directories...");
    const staleDirectories = await findDirectoriesWithDots(NODE_MODULES_DIR);

    if (staleDirectories.length === 0) {
        console.log("No stale directories detected.");
        return;
    }

    const plural = staleDirectories.length === 1 ? "directory" : "directories";
    console.log(`Removing ${staleDirectories.length} stale ${plural}...`);

    const failures = await removeDirectories(staleDirectories);

    if (failures.length > 0) {
        const failPlural = failures.length === 1 ? "directory" : "directories";
        console.warn("");
        console.warn(`${failures.length} ${failPlural} could not be removed. Close any programs that might be using them and rerun the cleanup.`);
        process.exitCode = 1;
    } else {
        console.log("Stale npm staging directories removed successfully.");
    }
}

main().catch(error => {
    console.error(`Cleanup failed: ${error.stack ?? error.message}`);
    process.exitCode = 1;
});
