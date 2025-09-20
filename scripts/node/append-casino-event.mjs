// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: green; icon-glyph: search-location;

/**
 * Casino Event CSV Appender for iOS Scriptable
 * 
 * This script is designed to run in the iOS Scriptable app and integrates with
 * the Casino Calendar project to add new casino events to the main CSV file.
 * 
 * USAGE:
 * - Run via iOS Shortcuts app with casino event data
 * - Input: JavaScript array of 6-item arrays
 * - Format: [EventName, Casino, Location, Offer, StartDate, EndDate]
 * 
 * DATA FORMAT REQUIREMENTS:
 * - Must be actual JavaScript array, not escaped string
 * - Each event must have exactly 6 items
 * - No escaped characters (\[, \], \$, etc.)
 * - Dates in format: "M/D/YYYY H:MM"
 * 
 * FEATURES:
 * - Duplicate detection based on Casino, StartDate, EndDate
 * - Data validation with detailed error messages
 * - iCloud file sync integration
 * - Comprehensive logging
 * 
 * INTEGRATION:
 * - Writes to: iCloud/CasinoEvents/casino_events.csv
 * - Compatible with Casino Calendar Dash app data loading
 * - Part of the overall casino event data management workflow
 */

// === CONFIGURATION ===

const folderName = "CasinoEvents";
const fileName = "casino_events.csv";
const headers = ["EventName", "Casino", "Location", "Offer", "StartDate", "EndDate"];
let logOutput = "";
function log(...args) {
    const message = args.join(" ");
    console.log(message);
    logOutput += message + "/n";
}

function parseCSVLine(line) {
    const regex = /"([^"]*(?:""[^""]*)*)"|([^,]+)/g;
    const result = [];
    let match;

    while ((match = regex.exec(line)) !== null) {
        const value = match[1] || match[2] || "";
        result.push(value.replace(/""/g, '"'));
    }

    return result;
}

function safeFolderName(casino, date) {
    return `${casino}`.replace(/[^\w\s-]/g, "").trim().replace(/\s+/g, "_") + "_" + date;
}

function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toISOString().split("T")[0];
}

// === EXECUTION ===
try {
    const fm = FileManager.iCloud();
    const dir = fm.joinPath(fm.documentsDirectory(), folderName);
    const filePath = fm.joinPath(dir, fileName);
    if (!fm.fileExists(dir)) fm.createDirectory(dir);

    let input = args.shortcutParameter;

    // If it's already an array, re-wrap it as object with events and images
    if (Array.isArray(input)) {
        input = { events: input, images: [] };
    }

    let events = input.events;
    let images = input.images || [];

    // Validate structure
    if (!Array.isArray(events)) {
        throw new Error("Input must be a JSON array of 6-item arrays.");
    }

    if (events.length === 0) {
        throw new Error("Events array is empty.");
    }

    // Validate that all events are arrays with correct structure
    for (let i = 0; i < events.length; i++) {
        if (!Array.isArray(events[i])) {
            throw new Error(`Event at index ${i} is not an array.`);
        }
        if (events[i].length !== headers.length) {
            throw new Error(`Event at index ${i} has ${events[i].length} items, expected ${headers.length}.`);
        }
    }

    // Download if file exists
    if (fm.isFileStoredIniCloud(filePath)) {
        await fm.downloadFileFromiCloud(filePath);
    }

    // Create file with headers if it doesn't exist
    if (!fm.fileExists(filePath)) {
        const headerRow = headers.join(",") + "\n";
        fm.writeString(filePath, headerRow);
    }

    // Read and parse existing CSV rows (excluding header)
    let existingCSV = fm.readString(filePath).split("\n").filter(line => line.trim() !== "");
    const existingRows = existingCSV.slice(1).map(parseCSVLine); // Remove header

    // Helper to build CSV row
    const formatRow = (event) =>
        event.map(f => `"${String(f).trim().replace(/"/g, '""')}"`).join(",");

    let newRows = "";
    let appendedCount = 0;
    let savedEventSummaries = [];

    function clean(val) {
        return String(val)
            .replace(/^"|"$/g, '')
            .replace(/\uFEFF/g, '')
            .replace(/\s+/g, ' ')
            .trim();
    }

    for (let i = 0; i < events.length; i++) {
        let event = events[i];
        // Note: Length validation already done above, so all events are guaranteed to have correct length

        const alreadyExists = existingRows.some(row => {
            const match =
                clean(row[1]) === clean(event[1]) &&
                clean(row[4]) === clean(event[4]) &&
                clean(row[5]) === clean(event[5]);

            if (match) {
                log(`❌ Duplicate found: \n CSV = ${clean(row[1])}, ${clean(row[4])}, ${clean(row[5])}\n Event = ${clean(event[1])}, ${clean(event[4])}, ${clean(event[5])}`);
            }

            return match;
        });

        if (alreadyExists) continue;

        // Append row
        const row = formatRow(event);
        newRows += row + "\n";
        appendedCount++;
        savedEventSummaries.push(`🎰 ${event[0]} @ ${event[1]} (${event[4]} – ${event[5]})`);

        // // Save associated images (commented out)
        // if (images[i] && Array.isArray(images[i])) {
        //     const [eventName, casino, , , startDate] = event;
        //     const subFolder = safeFolderName(casino, formatDate(startDate));
        //     const subFolderPath = fm.joinPath(dir, subFolder);
        //     if (!fm.fileExists(subFolderPath)) fm.createDirectory(subFolderPath);
        //     for (let j = 0; j < images[i].length; j++) {
        //         const imgData = Data.fromBase64String(images[i][j]);
        //         const imgPath = fm.joinPath(subFolderPath, `event_${i + 1}_img${j + 1}.jpg`);
        //         fm.write(imgPath, imgData);
        //         log(`🌁 Saved image: ${imgPath}`);
        //     }
        // }
    }

    const skippedCount = events.length - appendedCount;
    const summaryLog = savedEventSummaries.join("\n");

    if (appendedCount > 0) {
        fm.writeString(filePath, fm.readString(filePath) + newRows);
        Script.setShortcutOutput(`✅ ${appendedCount} new event(s) saved and ⛔️ ${skippedCount} duplicate event(s) skipped when adding to CSV. \n\n${summaryLog}\n\n${logOutput}`)
    } else {
        Script.setShortcutOutput(`⚠️ No new events saved. All ${skippedCount} provided event(s) already exist with the same Casino and time. \n\n${logOutput}`)
    }

} catch (err) {
    Script.setShortcutOutput(`❌ Failed: ${err.message} \n${logOutput}`);
}

Script.complete();