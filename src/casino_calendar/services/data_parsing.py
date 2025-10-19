"""Utilities for parsing and annotating event data before rendering."""

from collections import defaultdict
from datetime import timedelta
from math import floor

import pandas as pd
from casino_calendar.logging.config import setup_logger

# Initialize module logger
logger = setup_logger(__name__)


def annotate_events_with_flags(events_df, week_start, week_end):
    """Return events annotated with overflow flags and sorted for rendering."""
    logger.debug(
        "Annotating %d events with flags for week %s to %s",
        len(events_df),
        week_start,
        week_end,
    )

    events_df = events_df.copy()
    events_df["orig_index"] = events_df.index

    events_df["Duration"] = (events_df["EndDate"] - events_df["StartDate"]).dt.total_seconds()
    events_df["has_left_arrow"] = events_df["StartDate"] < week_start
    events_df["has_right_arrow"] = events_df["EndDate"] > week_end

    # Count overflow types
    left_arrows = events_df["has_left_arrow"].sum()
    right_arrows = events_df["has_right_arrow"].sum()
    both_arrows = (events_df["has_left_arrow"] & events_df["has_right_arrow"]).sum()

    logger.debug(
        "Overflow flags counted: left=%d right=%d both=%d",
        left_arrows,
        right_arrows,
        both_arrows,
    )

    def get_overflow_priority(row):
        if row["has_left_arrow"] and row["has_right_arrow"]:
            return 0
        if row["has_right_arrow"]:
            return 3
        if not row["has_left_arrow"] and not row["has_right_arrow"]:
            return 2
        return 1

    events_df["overflow_sort"] = events_df.apply(get_overflow_priority, axis=1)

    sorted_events = events_df.sort_values(
        by=["overflow_sort", "StartDate", "EndDate", "Duration", "Casino"],
        ascending=[True, True, True, False, True],
    ).reset_index(drop=True)

    logger.debug("Events annotated and sorted successfully")
    return sorted_events


def filter_week_events(events_df, week_start, week_end):
    """Return events that intersect the current week."""
    logger.debug("Filtering events for week %s to %s", week_start, week_end)

    filtered = events_df[
        (events_df["EndDate"] > week_start)
        & (events_df["StartDate"] < week_end)
        & ~(events_df["StartDate"] == week_end)
        & ~((events_df["StartDate"] < week_start) & (events_df["EndDate"] > week_end))
    ].copy()

    logger.debug("Filtered to %d events for current week", len(filtered))
    return filtered


def assign_event_rows(events_df, week_start):
    """Assign vertical grid rows to events without overlap."""
    logger.debug("Assigning grid rows for %d events", len(events_df))

    used_rows_by_day = {i: set() for i in range(7)}
    recurring_rows = defaultdict(int)
    current_row = 0
    row_nums = []

    for priority in sorted(events_df["overflow_sort"].unique()):
        group_df = events_df[events_df["overflow_sort"] == priority].sort_values(
            by=["StartDate", "EndDate", "Duration", "Casino"],
            ascending=[True, True, False, True],
        )

        for idx, row in group_df.iterrows():
            row = events_df.loc[idx]
            start_delta = (row["StartDate"] - week_start).total_seconds() / (24 * 3600)
            end_delta = (row["EndDate"] - week_start).total_seconds() / (24 * 3600)

            visible_start = max(start_delta, 0)
            visible_end = min(end_delta, 7)

            start_day = max(0, floor(visible_start))
            end_day = min(6, floor(visible_end - 1e-6))

            recurring_key = f"{row['EventName']}|{row['Casino']}|{row['StartDate'].time()}|{row['EndDate'].time()}"
            preferred_row = recurring_rows.get(recurring_key)
            row_assigned = False

            if preferred_row is not None and all(
                preferred_row not in used_rows_by_day[d] for d in range(start_day, end_day + 1)
            ):
                assigned_row = preferred_row
                row_assigned = True
            else:
                for r in range(current_row, 100):
                    if all(r not in used_rows_by_day[d] for d in range(start_day, end_day + 1)):
                        assigned_row = r
                        recurring_rows[recurring_key] = r
                        row_assigned = True
                        break

            if row_assigned:
                for d in range(start_day, end_day + 1):
                    used_rows_by_day[d].add(assigned_row)
                events_df.at[idx, "row_num"] = assigned_row
                row_nums.append(assigned_row)

        current_row = max(row_nums, default=current_row) + 1

    return events_df


def prepare_week_events(events_df, week_start, *, include_sunday_duplicates=False):
    """Return events filtered and annotated for a single week.

    Parameters
    ----------
    events_df : pd.DataFrame
        Raw events dataframe.
    week_start : datetime
        The start of the week being rendered.
    include_sunday_duplicates : bool, optional
        If ``True`` duplicate any events that continue into Sunday so
        the duplicate block can be rendered in the Sunday column.  This
        duplication happens **before** row assignment to avoid block
        overlaps.
    """

    week_end = week_start + timedelta(days=7)
    week_events = filter_week_events(events_df, week_start, week_end)
    annotated = annotate_events_with_flags(week_events, week_start, week_end)

    if include_sunday_duplicates:
        sunday_mask = (annotated["StartDate"].dt.weekday <= 5) & (annotated["EndDate"].dt.weekday == 6)

        if sunday_mask.any():
            dup = annotated[sunday_mask].copy()
            dup["StartDate"] = dup["EndDate"].dt.floor("D")
            dup["is_duplicate"] = True
            annotated = pd.concat([annotated, dup], ignore_index=True)

    return assign_event_rows(annotated, week_start)
