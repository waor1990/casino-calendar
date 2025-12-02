// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: green; icon-glyph: search-location;

/**
 * Casino Event API Poster for iOS Scriptable
 *
 * This script sends casino events directly to the Casino Calendar REST API
 * instead of writing CSV files to iCloud. Provide either a single event
 * object or an array of 6- or 7-item arrays matching the API schema:
 * [EventName, Casino, Location, Offer, StartDate, EndDate, (OfferType?)].
 * Dates should be parseable by JavaScript's Date constructor and will be
 * converted to ISO 8601 UTC (Z) before sending to the API.
 */

const apiUrl = "http://<your-ip>:5001/events";

const KEYWORDS = {
    giveaway_keywords: [
        "giveaway",
        "giveaways",
        "gift",
        "gifts",
        "redeem",
        "earbuds",
        "headphones",
        "luggage",
        "necklace",
        "bracelet",
        "earrings",
        "tool set",
        "barbuds",
        "t-shirt",
        "wearable",
        "cooler",
        "backpack",
        "camping set",
        "cookware",
        "outdoor stove",
        "fan",
        "fishing pole",
        "bathroom set",
        "john wayne",
        "frigidaire",
        "collection",
        "cash",
        "drawing",
        "sweepstakes",
        "hot seat",
        "prize",
        "scratcher",
        "bonus drawing",
        "win it",
        "winnings",
        "fortune wheel",
        "money",
        "bonanza",
        "red white drawings",
        "hourly",
    ],
    free_play_cash_drawing_keywords: [
        "free play",
        "slot play",
        "free-play",
        "promo play",
        "lucky bucks",
        "mystery bonus",
        "vault of riches",
        "kiosk game",
        "freeplay",
        "xtra rewards",
    ],
    multiplier_points_keywords: [
        "multiplier",
        "points",
        "x points",
        "status points",
        "points multiplier",
        "point multiplier",
    ],
    hotel_travel_dining_shopping_keywords: [
        "hotel",
        "stay",
        "rv",
        "cruise",
        "dining",
        "shopping",
        "buffet",
        "food",
        "restaurant",
        "meal",
        "discount",
        "merchandise",
        "spa",
        "travel",
        "trip",
        "room night",
        "complimentary night",
        "standard room",
        "complimentary stay",
        "double rewards",
        "% off",
    ],
    special_event_keywords: [
        "tournament",
        "event",
        "brunch",
        "reception",
        "fiesta",
        "party",
        "taco crawl",
        "special",
        "celebration",
        "invite",
        "parade",
        "festival",
        "show",
        "game",
        "bingo",
        "concert",
        "birthday",
    ],
    vehicle_car_giveaway_keywords: [
        "car",
        "toyota",
        "tundra",
        "volkswagen",
        "jetta",
        "kia k5",
        "dodge charger",
        "rv giveaway",
        "win an rv",
        "rv drawing",
        "atv",
        "truck",
        "land cruiser",
    ],
};

function escapeRegex(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function buildKeywordPattern(keys) {
    const wholeWords = [];
    const phrases = [];

    for (const key of keys) {
        if (/^[A-Za-z0-9]+$/.test(key)) {
            wholeWords.push(`\\b${escapeRegex(key)}\\b`);
        } else {
            phrases.push(escapeRegex(key));
        }
    }

    return new RegExp([...wholeWords, ...phrases].join("|"), "i");
}

function classifyOfferType(eventName, offer) {
    const nameText = (eventName ?? "").toString();
    const offerText = (offer ?? "").toString();

    const patterns = {
        vehicle: buildKeywordPattern(KEYWORDS.vehicle_car_giveaway_keywords),
        giveaway: buildKeywordPattern(KEYWORDS.giveaway_keywords),
        freePlay: buildKeywordPattern(KEYWORDS.free_play_cash_drawing_keywords),
        multiplier: buildKeywordPattern(KEYWORDS.multiplier_points_keywords),
        hospitality: buildKeywordPattern(KEYWORDS.hotel_travel_dining_shopping_keywords),
        special: buildKeywordPattern(KEYWORDS.special_event_keywords),
    };

    const contains = (regex) => regex.test(nameText) || regex.test(offerText);

    if (contains(patterns.vehicle)) return "Giveaway";
    if (contains(patterns.giveaway)) return "Giveaway";
    if (contains(patterns.freePlay)) return "Free-Play";
    if (contains(patterns.multiplier)) return "Point-Based";
    if (contains(patterns.hospitality)) return "Hospitality-Rewards";
    if (contains(patterns.special)) return "Special-Events";

    return "Offer";
}

function toIso(dateStr) {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) throw new Error(`Invalid date: ${dateStr}`);
    return date.toISOString();
}

function normalizeEvent(raw) {
    if (Array.isArray(raw)) {
        const [EventName, Casino, Location, Offer, StartDate, EndDate, OfferType] = raw;
        const classifiedOfferType = OfferType ?? classifyOfferType(EventName, Offer);
        return {
            EventName,
            Casino,
            Location,
            Offer,
            StartDate: toIso(StartDate),
            EndDate: toIso(EndDate),
            OfferType: classifiedOfferType,
        };
    }

    if (typeof raw === "object" && raw !== null) {
        const offerType =
            raw.OfferType || classifyOfferType(raw.EventName, raw.Offer || raw.EventName);
        return {
            ...raw,
            StartDate: toIso(raw.StartDate),
            EndDate: toIso(raw.EndDate),
            OfferType: offerType,
        };
    }

    throw new Error("Input must be an event object or array.");
}

async function postEvent(event) {
    const req = new Request(apiUrl);
    req.method = "POST";
    req.headers = { "Content-Type": "application/json" };
    req.body = JSON.stringify(event);
    return req.loadJSON();
}

async function run() {
    const input = args.shortcutParameter;
    const events = Array.isArray(input) ? input.map(normalizeEvent) : [normalizeEvent(input)];

    const results = [];
    for (const event of events) {
        const response = await postEvent(event);
        results.push(response);
    }

    const summary = results
        .map((evt) => `✅ ${evt.EventName} (${evt.Casino}) saved as ${evt.EventID}`)
        .join("\n");

    Script.setShortcutOutput(summary);
}

run().catch((err) => {
    Script.setShortcutOutput(`❌ Failed to save events: ${err.message}`);
});

Script.complete();
