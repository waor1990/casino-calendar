// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: yellow; icon-glyph: file-excel;

/**
 * Casino Event CSV Cleanup for iOS Scriptable
 * 
 * This script removes old casino events from the CSV file to prevent it from
 * growing too large over time. It integrates with the Casino Calendar project
 * data management workflow.
 * 
 * USAGE:
 * - Run periodically in iOS Scriptable app (manually or via automation)
 * - No input required - automatically processes the existing CSV file
 * 
 * CLEANUP CRITERIA:
 * - Removes events where EndDate is older than 2 months
 * - Uses robust date parsing for M/D/YYYY H:MM format
 * - Preserves events with invalid/unparseable dates (safety first)
 * 
 * FEATURES:
 * - Casino-specific removal counting and reporting
 * - Robust CSV parsing with proper quote handling
 * - Alert dialog showing detailed removal summary
 * - iCloud file sync integration
 * - Safe date parsing with fallback handling
 * 
 * INTEGRATION:
 * - Reads/writes: iCloud/CasinoEvents/casino_events.csv
 * - Compatible with Casino Calendar Dash app data loading
 * - Works alongside AppendCasinoEventToCSV.js for complete data lifecycle
 * - Part of the overall casino event data management workflow
 * 
 * SAFETY:
 * - Preserves file structure and CSV formatting
 * - Only removes events with valid, old end dates
 * - Shows summary before completion via alert dialog
 */

// File: trimOldCasinoEvents.js

const fm = FileManager.iCloud();
const folderPath = fm.joinPath(fm.documentsDirectory(), "CasinoEvents");
const filePath = fm.joinPath(folderPath, "casino_events.csv");

function parseCSVLine(line) {
  const result = [];
  let inQuotes = false;
  let field = '';
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    const nextChar = line[i + 1];
    
    if (char === '"' && inQuotes && nextChar === '"') {
      field += '"';
      i++
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(field.trim());
      field = '';
    } else {
      field += char;
    }
  }
  
  result.push(field.trim());
  return result;
}

//  Wait for iCloud sync
if (!fm.isFileStoredIniCloud(filePath)) {
  await fm.downloadFileFromiCloud(filePath);
}

const csv = fm.readString(filePath);
const lines = csv.trim().split("\n");
const header = parseCSVLine(lines[0]);

//  Get relevant column indexes
const endDateIndex = header.indexOf("EndDate");
const casinoIndex = header.indexOf("Casino");

if (endDateIndex === -1 || casinoIndex === -1) {
  throw new Error("Missing required columns: EndDate or Casino");
}

function parseMDYDateTime(str) {
//   Supports 24-hour datetime formats
  const match = str.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})(?:\s+(\d{1,2}):(\d{2}))?$/);
  if (!match) return null;
  const [, month, day, year, hour = "0", minute = "0"] = match;
  return new Date(
    Number(year),
    Number(month) - 1,
    Number(day),
    Number(hour),
    Number(minute)
  );
}

//  Get cutoff date (2 months ago)
const today = new Date();
const cutoff = new Date(today.setMonth(today.getMonth() - 2));

// Filter lines and collect removed counts
const kept = [lines[0]];
const removedByCasino = {};

for (let i = 1; i < lines.length; i++) {
  const cols = parseCSVLine(lines[i]);
  const endDateStr = cols[endDateIndex];
  const casino = cols[casinoIndex].trim();
  const endDate = parseMDYDateTime(endDateStr);
  
  if (!endDate || isNaN(endDate.getTime()) || endDate >= cutoff) {
    kept.push(lines[i]);
  } else {
    removedByCasino[casino] = (removedByCasino[casino] || 0) + 1;
  }
}

// Overwrite the file
fm.writeString(filePath, kept.join("\n"));

// Build Summary
let summary = "Removed Events by Casino:\n";
if (Object.keys(removedByCasino).length === 0) {
  summary += "No old events removed.";
} else {
  for (let [casino, count] of Object.entries(removedByCasino)) {
    summary += `• ${casino}: ${count}\n`;
  }
}

// Show result
const alert = new Alert();
alert.title = "Cleanup Complete";
alert.message = summary.trim();
await alert.present();