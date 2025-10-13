#!/usr/bin/env node
/**
 * Validate package.json to ensure it contains valid JSON and no merge artifacts.
 */
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, "..", "..");
const PACKAGE_JSON_PATH = path.join(PROJECT_ROOT, "package.json");

const CONFLICT_MARKERS = ["<<<<<<<", "=======", ">>>>>>>"];

function formatMessage(message) {
    return `package.json validation failed: ${message}`;
}

async function readPackageJson() {
    try {
        return await fs.readFile(PACKAGE_JSON_PATH, "utf8");
    } catch (error) {
        if (error.code === "ENOENT") {
            throw new Error("package.json was not found in the project root.");
        }
        throw new Error(`unable to read package.json (${error.code ?? error.message})`);
    }
}

function checkForConflictMarkers(contents) {
    for (const marker of CONFLICT_MARKERS) {
        if (contents.includes(marker)) {
            throw new Error(
                `detected Git merge conflict markers (e.g. '${marker}'). Resolve the merge conflict and rerun the installer.`,
            );
        }
    }
}

function validateJson(contents) {
    try {
        JSON.parse(contents);
    } catch (error) {
        const message = error instanceof SyntaxError ? error.message : String(error);
        throw new Error(`could not parse package.json (${message}).`);
    }
}

async function main() {
    const contents = await readPackageJson();
    checkForConflictMarkers(contents);
    validateJson(contents);
    if (process.argv.includes("--quiet")) {
        return;
    }
    console.log("package.json looks valid.");
}

main().catch(error => {
    console.error(formatMessage(error.message));
    process.exitCode = 1;
});
