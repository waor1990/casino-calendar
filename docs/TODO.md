# Casino Calendar - Data Handling Review & Refactor Tasks

This document contains a comprehensive analysis of all data handling components in the codebase, identifying areas for improvement in clarity, maintainability, and correctness.

## Data Handling Components Analysis

### Core Data Processing Modules

#### **1. `app_components/data.py` - Primary Data Loading & Processing**

**Current State:** ✅ **Well-structured with good error handling**

- **Functionality:** CSV loading, timezone conversion (PDT→UTC), offer type categorization
- **Strengths:**
  - Comprehensive DST handling (AmbiguousTimeError, NonExistentTimeError)
  - Good logging throughout data processing pipeline
  - JSON-based keyword categorization system
  - Proper error handling for file operations
- **Areas for Improvement:**
  - `categorize_offer_type_updated()` has high complexity (nested conditionals)
  - File I/O operations could be extracted to separate functions
  - Large function could be broken into smaller, focused methods

#### **2. `utils/data_parsing.py` - Event Processing & Grid Layout**

**Current State:** ⚠️ **Complex algorithms needing refactor**

- **Functionality:** Event filtering, overflow annotations, row assignment for grid layout
- **Strengths:**
  - Modular functions with clear separation of concerns
  - Good logging for debugging complex grid layouts
  - Efficient row assignment algorithm prevents overlaps
- **Critical Issues:**
  - `assign_event_rows()` has complex nested loops (O(n²) in worst case)
  - Magic numbers scattered throughout (e.g., range(current_row, 100))
  - `recurring_key` string generation is fragile and hard to maintain
  - `get_overflow_priority()` logic embedded in annotation function

#### **3. `app_components/utils.py` - Timezone & Data Utilities**

**Current State:** ✅ **Solid utility functions**

- **Functionality:** Timezone conversions, date range calculations, text truncation
- **Strengths:**
  - Clean, focused utility functions
  - Proper DST handling in `get_week_range()`
  - Type hints and clear documentation
- **Minor Issues:**
  - `build_event_info_rows()` mixes data processing with HTML generation
  - Error handling could be more explicit in timestamp conversion

#### **4. `utils/colors.py` - Color Data Management**

**Current State:** ✅ **Simple and effective**

- **Functionality:** JSON-based color mapping for casinos
- **Strengths:**
  - Good error handling for missing files
  - Clean separation of color logic
- **Minor Issues:**
  - Fallback color generation could be more sophisticated

### Callback Data Processing

#### **5. `app_components/callbacks/filters.py` - Filter & Navigation Logic**

**Current State:** ⚠️ **Complex data transformations in callbacks**

- **Functionality:** Week navigation, casino filtering, overflow event handling
- **Strengths:**
  - Good separation between UI logic and data filtering
  - Proper datetime calculations for week boundaries
- **Issues:**
  - Data filtering logic scattered across multiple callbacks
  - Complex datetime calculations repeated in multiple places
  - DataFrame operations mixed with UI logic in `render_single_week_chart()`

#### **6. `app_components/callbacks/events.py` - Event Modal Logic**

**Current State:** ⚠️ **Data access patterns need improvement**

- **Functionality:** Day view generation, event modal data preparation
- **Issues:**
  - Unsafe data access patterns (recently fixed but patterns still fragile)
  - Complex date filtering logic duplicated from plotting module
  - Casino filtering logic repeated across multiple functions

#### **7. `app_components/plotting.py` - Day View Data Processing**

**Current State:** ⚠️ **Complex data processing mixed with UI generation**

- **Functionality:** Event overlap resolution, time-based filtering, track assignment
- **Strengths:**
  - Sophisticated track assignment algorithm
  - Good handling of multi-day events and boundaries
- **Critical Issues:**
  - `generate_day_view_html()` is monolithic (200+ lines)
  - Data processing mixed with HTML generation
  - Complex filtering logic that should be extracted to utils
  - Redundant timezone conversions and boundary calculations

### Data Flow Issues

#### **8. Data Validation & Type Safety**

**Current State:** ❌ **Missing comprehensive validation**

- **Missing:** Input validation for CSV data integrity
- **Missing:** Type hints in several key functions
- **Missing:** Data schema validation for JSON configuration files

#### **9. Performance Bottlenecks**

**Current State:** ⚠️ **Several optimization opportunities**

- **Issue:** Repeated pandas DataFrame copying in processing pipeline
- **Issue:** JSON file loading on every function call in `categorize_offer_type_updated()`
- **Issue:** Complex DataFrame filtering repeated across modules

## Priority 1 Refactor Tasks (Critical)

### Data Processing Architecture

- [ ] **Extract data processing from UI components** - Move all DataFrame operations from `plotting.py` to dedicated data processing utilities
- [ ] **Break up monolithic functions** - Split `generate_day_view_html()` into data processing and UI generation components
- [ ] **Centralize filtering logic** - Create unified filtering utilities to eliminate duplication across callbacks
- [ ] **Optimize row assignment algorithm** - Refactor `assign_event_rows()` for better performance and maintainability

### Data Validation & Type Safety

- [ ] **Add input validation** - Validate CSV structure and data types before processing
- [ ] **Implement data schemas** - Add Pydantic models or similar for data validation
- [ ] **Complete type hint coverage** - Add type hints to all data processing functions
- [ ] **Add data integrity tests** - Test edge cases for malformed data, timezone boundaries

### Error Handling & Resilience

- [ ] **Centralized error handling** - Create consistent error handling patterns across data processing modules
- [ ] **Graceful degradation** - Ensure app continues working with partial data failures
- [ ] **Add data recovery mechanisms** - Handle corrupted data files gracefully

## Priority 2 Refactor Tasks (Important)

### Performance Optimization

- [ ] **Cache JSON data loading** - Load offer keywords and color data once at startup
- [ ] **Optimize DataFrame operations** - Reduce unnecessary copying and filtering operations
- [ ] **Implement data preprocessing** - Cache processed data structures to avoid repeated calculations

### Code Organization

- [ ] **Create data models** - Define clear data structures for events, casinos, offers
- [ ] **Extract business logic** - Move offer categorization and business rules to dedicated modules
- [ ] **Standardize data interfaces** - Create consistent APIs between data processing modules

### Testing Coverage

- [ ] **Add comprehensive data processing tests** - Test all edge cases in filtering and processing logic
- [ ] **Add performance regression tests** - Ensure data processing remains performant
- [ ] **Add integration tests** - Test complete data flow from CSV to UI

## Priority 3 Refactor Tasks (Enhancement)

### UI / UX

- [ ] Add hover tooltips on grid events similar to the legacy Plotly chart
- [x] ✅ Allow clicking on empty day areas to open the day view
- [ ] Refine mobile scaling and text truncation for very small screens

### Event Logic

- [x] ✅ Improve handling of overnight events that cross DST boundaries
- [x] ✅ Validate duplication logic for Saturday-to-Sunday mini-blocks

### Testing

- [ ] Parametrize modal behavior tests
- [x] ✅ Add edge cases for timezone conversions

### Data Features

- [ ] **Add data export functionality** - Allow users to export filtered event data
- [ ] **Implement data caching** - Cache processed event data for better performance
- [ ] **Add data validation UI** - Show data quality issues in admin interface

## Implementation Guidelines

### Refactor Approach

1. **Start with data model definitions** - Create clear interfaces before refactoring implementations
2. **Extract pure functions first** - Move data processing logic to utility modules
3. **Maintain backward compatibility** - Ensure existing functionality continues working
4. **Add tests before refactoring** - Ensure behavior is preserved during changes

### Code Quality Standards

- **Single Responsibility Principle** - Each function should have one clear purpose
- **Pure Functions Preferred** - Avoid side effects in data processing functions
- **Explicit Error Handling** - Handle edge cases explicitly rather than relying on defaults
- **Performance Awareness** - Consider data size and processing complexity

### Testing Strategy

- **Unit tests for pure functions** - Test data processing logic in isolation
- **Integration tests for data flow** - Test complete data processing pipelines
- **Edge case coverage** - Test timezone boundaries, malformed data, empty datasets
- **Performance benchmarks** - Monitor processing time for large datasets

---

**Next Steps:** Begin with Priority 1 tasks, focusing on extracting data processing logic from UI components and establishing clear data validation patterns.
