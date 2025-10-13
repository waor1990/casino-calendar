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

async function removeDirectories(directories) {
    const failures = [];

    directories.sort((a, b) => b.length - a.length);

    for (const directory of directories) {
        try {
            await fs.rm(directory, { recursive: true, force: true });
            console.log(`  ✔ Removed ${formatRelative(directory)}`);
        } catch (error) {
            failures.push({ directory, error });
            console.warn(`  ✖ Failed to remove ${formatRelative(directory)} (${error.code ?? error.message})`);
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
