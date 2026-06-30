# Requirements Document

## Introduction

This feature redesigns the Reports page of the Spotify VoC (Voice of Customer) Intelligence Platform. The current implementation renders raw JSON output from AI analysis in expandable `<pre>` blocks. The redesign transforms the Reports page into a polished AI analytics dashboard where every insight is visual, scannable, and presentation-ready — inspired by Linear, Notion AI, Vercel Dashboard, and Perplexity. The system uses a modular component rendering layer that maps structured JSON insight objects to purpose-built UI components.

## Glossary

- **Report_Viewer**: The main page component that renders a full AI-generated report with all its sections and insights
- **Rendering_Layer**: The modular mapping system that receives structured JSON from the backend and dispatches each section to the appropriate UI component
- **Insight_Section**: A discrete block of the report corresponding to one AI workflow result (e.g., pain points, feature requests, sentiment analysis)
- **Metric_Card**: A compact card component displaying a single numeric KPI with label and optional trend indicator
- **Insight_Card**: A generic card component for displaying a single insight item with title, description, supporting data, and metadata badges
- **Section_Header**: A component that introduces each report section with a title, icon, and optional description
- **Confidence_Badge**: A visual indicator showing the AI confidence score for a given insight using color coding
- **Severity_Badge**: A color-coded badge indicating the severity level (Critical, High, Medium, Low) of a pain point or issue
- **Priority_Badge**: A badge indicating the priority level of a recommendation or feature request
- **Chart_Card**: A container component for rendering data visualizations (pie charts, bar charts, trend lines)
- **Skeleton_Loader**: A placeholder UI component that mimics the final layout shape while data is loading
- **Empty_State**: A component shown when a report section contains no data, providing context and guidance
- **Source_Badge**: A small labeled badge indicating the data source (Reddit, App Store, Play Store, etc.)

## Requirements

### Requirement 1: Report Header Rendering

**User Story:** As a Product Manager, I want to see a clear report header with metadata at the top of every report, so that I can immediately understand what data was analyzed and when.

#### Acceptance Criteria

1. WHEN a report is loaded, THE Report_Viewer SHALL render a header section displaying the report title, creation date formatted as a human-readable date string, the list of sources used, total review count, AI model name from the report's insights, and the report generation timestamp
2. WHEN the user clicks the Export button in the header, THE Report_Viewer SHALL trigger a browser file download of a JSON file containing the report title, description, creation date, workflows, sources, review count, and all associated insight content, with the filename formatted as "report_{id}.json"
3. WHEN the user clicks the Regenerate button in the header, THE Report_Viewer SHALL initiate a new insight generation request using the original report's workflows, sources, and date range parameters
4. THE Report_Viewer SHALL display each source in the report's sources list as a Source_Badge component within the header, rendering one badge per source
5. IF the report data fails to load, THEN THE Report_Viewer SHALL display an error message indicating the report could not be retrieved and SHALL NOT render the Export or Regenerate buttons

### Requirement 2: Executive Summary Section

**User Story:** As a Product Manager, I want to see a prominent executive summary card at the top of the report, so that I can grasp the overall findings at a glance.

#### Acceptance Criteria

1. WHEN the report contains an executive_summary insight, THE Report_Viewer SHALL render a full-width visually distinct card above all other insight sections, displaying the bottom-line summary, up to 5 key findings (themes), the key metric, overall sentiment, and a Confidence_Badge
2. THE Executive_Summary_Card SHALL display each key finding as a labeled item showing the theme name, severity (1–5), frequency (High/Medium/Low), and a one-line description
3. THE Executive_Summary_Card SHALL display the overall sentiment using a color-coded indicator (green for Positive, amber for Mixed, red for Negative)
4. THE Executive_Summary_Card SHALL display the key metric as a highlighted inline statistic within the card
5. WHEN the executive_summary insight is not present in the report, THE Report_Viewer SHALL display an Empty_State component in the executive summary position with a message indicating that no executive summary was generated

### Requirement 3: Key Metrics Row

**User Story:** As a Product Manager, I want to see high-level numeric metrics in a scannable row of cards, so that I can quickly assess the quantitative state of user feedback.

#### Acceptance Criteria

1. WHEN the report is loaded, THE Report_Viewer SHALL render a horizontal row of exactly 8 Metric_Card components showing: Total Reviews (integer count), Average Rating (numeric to 1 decimal place on a 1–5 scale), Positive percentage, Negative percentage, Neutral percentage (each displayed as an integer percentage with "%" suffix), Topics Found (integer count), Feature Requests count (integer count), and Bug Reports count (integer count)
2. THE Metric_Card components SHALL derive their values from the report metadata (review_count, date range) and aggregated insight content (sentiment distribution from sentiment_analysis, topic count from theme_clustering, feature and bug counts from respective workflow results)
3. WHILE the viewport width is below 768px, THE Report_Viewer SHALL stack the Metric_Card components into a single-column vertical layout
4. IF a metric value cannot be computed due to missing insight data, THEN THE Metric_Card SHALL display a dash character ("—") in place of the numeric value and remain visible in the row
5. WHEN the report contains more than 9,999 total reviews, THE Metric_Card for Total Reviews SHALL display the count in abbreviated format with one decimal (e.g., "10.0K", "1.2M")

### Requirement 4: Sentiment Analysis Section

**User Story:** As a Product Manager, I want to visualize sentiment distribution with charts and highlight cards, so that I can understand the emotional landscape of user feedback.

#### Acceptance Criteria

1. WHEN the report contains a sentiment_analysis insight, THE Report_Viewer SHALL render a section with three Insight_Card components: one for Positive Drivers displaying the positive_drivers list, one for Negative Drivers displaying the negative_drivers list, and one for Notable Shifts displaying the notable_shifts text
2. WHEN the sentiment_analysis insight contains an overall_sentiment object with positive_pct, neutral_pct, and negative_pct values, THE Report_Viewer SHALL render a pie chart within a Chart_Card component showing the three sentiment segments with their percentage labels
3. WHEN the sentiment_analysis insight contains a by_topic array with at least one entry, THE Report_Viewer SHALL render a bar chart within a Chart_Card component showing positive, neutral, and negative counts per topic for up to 10 topics ordered by total count descending
4. WHEN the sentiment_analysis insight contains a sentiment_drivers object, THE Report_Viewer SHALL render the positive_drivers and negative_drivers as separate labeled lists within individual Insight_Card components
5. IF the report does not contain a sentiment_analysis insight, THEN THE Report_Viewer SHALL display an Empty_State component in the Sentiment Analysis section position

### Requirement 5: Pain Points Section

**User Story:** As a Product Manager, I want pain points displayed as individual severity-coded cards with supporting evidence, so that I can prioritize the most impactful user problems.

#### Acceptance Criteria

1. WHEN the report contains a pain_points insight with one or more pain point items, THE Report_Viewer SHALL render each pain point as an individual Insight_Card displaying: title, severity (1-5), frequency (mention count), category, AI explanation, and Severity_Badge
2. THE Pain_Points_Section SHALL display a Severity_Badge on each card showing the label "Critical" for severity 5, "High" for severity 4, "Medium" for severity 2-3, and "Low" for severity 1, color-coded red for severity 4-5, amber for severity 2-3, and green for severity 1
3. THE Pain_Points_Section SHALL order pain point cards by the product of severity multiplied by frequency in descending order, using severity as the tiebreaker when two cards have equal products
4. WHEN a pain point card includes a non-empty representative_quotes array, THE Report_Viewer SHALL render the first quote in a styled callout block within the card
5. IF the pain_points insight contains an empty pain_points array or the pain_points key is absent from the report, THEN THE Report_Viewer SHALL display an Empty_State component indicating no pain points were identified

### Requirement 6: Feature Requests Section

**User Story:** As a Product Manager, I want feature requests displayed as prioritized cards showing user demand and business value, so that I can make informed roadmap decisions.

#### Acceptance Criteria

1. WHEN the report contains a feature_requests insight, THE Report_Viewer SHALL render each feature request as an Insight_Card displaying: title, description, request count, complexity estimate (Low, Medium, or High), business value (Low, Medium, or High), and a comma-separated list of user segments
2. THE Feature_Requests_Section SHALL display a Priority_Badge on each card with one of three levels — High, Medium, or Low — where High requires both request count ≥ 10 and business value of High, Low requires request count < 5 or business value of Low, and Medium applies to all other combinations
3. THE Feature_Requests_Section SHALL display the first representative quote from the feature request data in a visually distinct callout block within each card, offset from surrounding content by background color or border
4. THE Feature_Requests_Section SHALL display Insight_Cards sorted in descending order by Priority_Badge level (High first, then Medium, then Low), with cards of equal priority sorted by request count descending
5. IF the feature_requests insight contains an empty feature_requests array, THEN THE Feature_Requests_Section SHALL display an empty-state message indicating no feature requests were identified

### Requirement 7: Emerging Trends Section

**User Story:** As a Product Manager, I want to see emerging trends as cards highlighting growth signals and time horizons, so that I can anticipate where user feedback is headed.

#### Acceptance Criteria

1. WHEN the report contains an emerging_trends insight, THE Report_Viewer SHALL render each trend as an Insight_Card with trend name, description, growth signal, potential impact, time horizon, and Confidence_Badge, ordered by potential impact level descending
2. THE Emerging_Trends_Section SHALL display potential impact as a color-coded badge using three levels: High (red), Medium (amber), and Low (green)
3. WHEN the emerging_trends insight includes a watch list, THE Report_Viewer SHALL render watch-list items as visually de-emphasized cards (smaller text and muted gray styling) below the main trend cards
4. WHEN the report does not contain an emerging_trends insight, THE Report_Viewer SHALL display an Empty_State component in the emerging trends position

### Requirement 8: Theme Clusters Section

**User Story:** As a Product Manager, I want to see how feedback naturally clusters into themes, so that I can understand the key topic areas users discuss.

#### Acceptance Criteria

1. WHEN the report contains a theme_clustering insight with one or more clusters, THE Report_Viewer SHALL render each theme cluster as a card displaying theme name, review count (as a numeric label), sentiment mix indicator (distinguishing "Mostly Positive", "Mixed", and "Mostly Negative"), and key insight text, ordered by review count descending
2. THE Theme_Clusters_Section SHALL display sub-themes as tag chips within each cluster card, showing a maximum of 8 sub-theme chips
3. WHEN a cluster card includes representative quotes, THE Report_Viewer SHALL display up to 3 quotes in a collapsed-by-default expandable section within the card
4. WHEN the theme_clustering insight includes cross_cutting_themes, THE Report_Viewer SHALL display them as a distinct group of tag chips above or below the cluster cards, labeled to indicate these themes span multiple clusters
5. IF the theme_clustering insight contains an empty clusters array, THEN THE Report_Viewer SHALL display an empty-state message indicating no theme clusters were identified

### Requirement 9: Jobs To Be Done Section

**User Story:** As a Product Manager, I want to understand the jobs users are hiring Spotify for, so that I can align product development with actual user motivations.

#### Acceptance Criteria

1. WHEN the report contains a jobs_to_be_done insight, THE Report_Viewer SHALL render each job as an Insight_Card displaying the job statement (situation, motivation, expected outcome), the satisfaction indicator, a list of up to 10 barriers, and a list of up to 10 workarounds
2. THE Jobs_To_Be_Done_Section SHALL display a color-coded satisfaction indicator for each job: green when satisfaction is "Satisfied", amber when satisfaction is "Partially Satisfied", and red when satisfaction is "Unsatisfied", where the satisfaction value is derived from the insight data returned by the backend
3. WHEN underserved jobs are identified (jobs with satisfaction equal to "Unsatisfied" or "Partially Satisfied"), THE Report_Viewer SHALL highlight them by rendering those Insight_Cards with a visually differentiated border or background that contrasts with non-highlighted cards
4. IF the report contains a jobs_to_be_done section but it includes zero job entries, THEN THE Report_Viewer SHALL display an empty-state message indicating that no jobs-to-be-done were identified in the analyzed feedback

### Requirement 10: Competitor Mentions Section

**User Story:** As a Product Manager, I want to see which competitors users mention and in what context, so that I can understand competitive positioning.

#### Acceptance Criteria

1. WHEN the report contains a competitor_mentions insight, THE Report_Viewer SHALL render each competitor as an Insight_Card displaying competitor name, mention count, sentiment toward the competitor (Positive, Neutral, or Negative), context summary, perceived advantage, and representative quotes, ordered by mention count in descending order
2. WHEN the competitor_mentions insight includes switching signals, THE Competitor_Mentions_Section SHALL render each switching signal as a card in a labeled sub-section below the competitor overview, displaying the signal text, target competitor, and switching reason
3. WHEN the competitor_mentions insight includes competitive advantages for Spotify, THE Competitor_Mentions_Section SHALL display them as a list within a green-accented callout block indicating retained strengths
4. WHEN the competitor_mentions insight contains no switching signals or no competitive advantages, THE Competitor_Mentions_Section SHALL omit the corresponding sub-section without displaying an Empty_State for that sub-section

### Requirement 11: User Personas Section

**User Story:** As a Product Manager, I want data-driven user personas presented visually, so that I can empathize with distinct user segments and their specific needs.

#### Acceptance Criteria

1. WHEN the report contains a user_personas insight, THE Report_Viewer SHALL render each persona as a visually distinct card occupying full container width (single-column layout), displaying persona name, description, listening behavior, primary need, main frustration, discovery approach, churn risk, and representative quote
2. THE User_Personas_Section SHALL display churn risk using a color-coded badge (red for High, amber for Medium, green for Low)
3. THE User_Personas_Section SHALL display the estimated size as a labeled value on each persona card
4. THE User_Personas_Section SHALL display the representative quote in a visually distinct block (e.g., italic, indented, or bordered) to differentiate it from descriptive text
5. IF the user_personas insight contains an empty personas array, THEN THE User_Personas_Section SHALL display an empty state message indicating no personas were generated
6. IF a persona object is missing any optional field (listening behavior, discovery approach, or representative quote), THEN THE Report_Viewer SHALL omit that field from the card without rendering blank or broken layout elements

### Requirement 12: Product Recommendations Section

**User Story:** As a Product Manager, I want actionable product recommendations with clear prioritization, so that I can translate user feedback into roadmap items.

#### Acceptance Criteria

1. WHEN the report contains a product_recommendations insight, THE Report_Viewer SHALL render each recommendation as a full-width Insight_Card displaying title, description, rationale, impact score (1–10), effort score (1–10), confidence score (1–10), calculated ICE score (impact × confidence ÷ effort), affected personas as a comma-separated list, and success metric
2. THE Product_Recommendations_Section SHALL display impact, effort, and confidence scores as horizontal progress bars filled proportionally to the score value on a 1-to-10 scale, with the numeric score displayed adjacent to each bar
3. THE Product_Recommendations_Section SHALL sort recommendations by ICE score in descending order
4. WHEN the insight includes quick_wins and strategic_bets arrays, THE Report_Viewer SHALL render them in separate sub-sections with a visible heading label ("Quick Wins", "Strategic Bets") and a distinguishing left-border color accent per sub-section
5. IF the product_recommendations insight contains an empty recommendations array, THEN THE Product_Recommendations_Section SHALL display an empty-state message indicating no recommendations were generated

### Requirement 13: Modular Rendering Layer

**User Story:** As a developer, I want a modular rendering system that maps JSON insight objects to UI components, so that new insight types can be added without modifying existing code.

#### Acceptance Criteria

1. THE Rendering_Layer SHALL accept a workflow type string (one of the values defined in AVAILABLE_WORKFLOWS) and a JSON content object (maximum depth of 10 levels), and return the corresponding React component registered for that workflow type
2. WHEN the Rendering_Layer receives an unrecognized workflow type, THE Rendering_Layer SHALL render a fallback component that displays the full JSON content object in a formatted, human-readable hierarchical view
3. THE Rendering_Layer SHALL use a component registry pattern where each workflow type maps to a specific renderer component, such that registering a new workflow type requires adding only a single registry entry and a new renderer component without modifying existing renderer components or the core rendering function
4. IF the Rendering_Layer receives a null, undefined, or empty content object, THEN THE Rendering_Layer SHALL render an empty-state indicator in place of the workflow-specific component
5. WHEN a new workflow type is registered, THE Rendering_Layer SHALL render the new workflow type using its registered renderer component without requiring changes to any previously registered renderer components or to the registry lookup logic

### Requirement 14: Reusable Component Architecture

**User Story:** As a developer, I want a library of reusable report components, so that the report sections are consistent in style and behavior.

#### Acceptance Criteria

1. THE Report_Viewer SHALL use a shared set of reusable components including: Section_Header, Metric_Card, Insight_Card, Chart_Card, Confidence_Badge, Severity_Badge, Priority_Badge, Source_Badge, and Empty_State
2. THE Insight_Card component SHALL accept props for title (maximum 120 characters displayed), description, an array of metadata badges (maximum 5 badges), an optional supporting quote, and an optional list of action items (maximum 10 items), rendering them in a fixed vertical order: title, badges, description, quote, action items
3. THE Section_Header component SHALL accept a title, a lucide-react icon, and an optional description, rendering a heading with the icon displayed inline to the left of the title text and the description rendered below the title when provided
4. IF an optional prop (description, supporting quote, or action items) is null or undefined, THEN THE component SHALL omit that element from the rendered output without displaying empty space or placeholder content
5. THE Confidence_Badge component SHALL accept a numeric score from 0 to 100 and display it with color coding: green for 80–100, amber for 50–79, and red for 0–49
6. THE Severity_Badge component SHALL accept a numeric level from 1 to 5 and display it with color coding: red for levels 4–5, amber for levels 2–3, and green for level 1

### Requirement 15: Loading States

**User Story:** As a user, I want to see skeleton loading placeholders while report data is being fetched, so that I have visual feedback that the page is working.

#### Acceptance Criteria

1. WHILE the report data is being fetched, THE Report_Viewer SHALL display Skeleton_Loader components that occupy the same grid positions and approximate dimensions as the final rendered content for each visible report section (header, metrics row, and insight sections)
2. THE Skeleton_Loader components SHALL animate with a repeating shimmer effect cycling every 1.5 to 2 seconds to indicate active loading
3. WHEN the report data fetch completes successfully, THE Report_Viewer SHALL replace the Skeleton_Loader components with the final rendered content with zero visible repositioning of surrounding elements (no cumulative layout shift)
4. IF the report data fetch fails or does not complete within 30 seconds, THEN THE Report_Viewer SHALL replace the Skeleton_Loader components with an error message indicating the failure and offering a retry action
5. WHEN the user activates the retry action on the error state, THE Report_Viewer SHALL re-initiate the data fetch and display the Skeleton_Loader components again

### Requirement 16: Empty States

**User Story:** As a user, I want to see helpful messages when a report section has no data, so that I understand why it is empty and what to do.

#### Acceptance Criteria

1. WHEN a report section's insight data array is empty or contains no entries for a given workflow, THE Report_Viewer SHALL display an Empty_State component containing: an icon relevant to the section type, a message identifying which workflow or section has no data, and an actionable suggestion directing the user to generate insights for that section
2. THE Empty_State component SHALL occupy a minimum height of 120 pixels and SHALL NOT display raw API error strings, stack traces, or render as a blank container with no visible content
3. IF the Report_Viewer fails to retrieve insight data due to a network or server error, THEN THE Report_Viewer SHALL display an error-specific Empty_State indicating that data could not be loaded and suggesting the user retry the action
4. WHILE report detail data is being fetched, THE Report_Viewer SHALL display a loading skeleton or indicator distinguishable from the Empty_State component, so that users can differentiate between a loading state and a confirmed absence of data

### Requirement 17: Mobile Responsive Layout

**User Story:** As a Product Manager viewing reports on a tablet or phone, I want the report layout to adapt to smaller screens, so that I can review insights on any device.

#### Acceptance Criteria

1. WHILE the viewport width is below 768px, THE Report_Viewer SHALL stack all card grids into a single column layout
2. WHILE the viewport width is below 768px, THE Chart_Card components SHALL resize their charts to fit the available width without horizontal scrolling and SHALL maintain a minimum chart height of 200px
3. THE Report_Viewer SHALL render text at a minimum font size of 14px and SHALL render all interactive elements with a minimum touch target size of 44×44px on all viewport widths from 320px to 1920px
4. WHILE the viewport width is below 768px, THE Report_Viewer SHALL ensure no content overflows the viewport horizontally, requiring zero horizontal scroll to access any report element

### Requirement 18: Visual Design Standards

**User Story:** As a Product Manager, I want the report to have a premium, modern feel with generous whitespace, so that the information is easy to scan and pleasant to read.

#### Acceptance Criteria

1. THE Report_Viewer SHALL use cards, badges, progress bars, callouts, and charts as primary display elements with no data tables for insight presentation
2. THE Report_Viewer SHALL apply consistent spacing of at least 24px between major sections (each insight workflow output constitutes a major section) and 16px between cards within a section
3. THE Report_Viewer SHALL use color-coded elements to communicate severity (red), success (green), warning (amber), and neutral (gray) states, and SHALL pair each color-coded element with a text label or icon so that state meaning is conveyed without relying on color alone
4. THE Report_Viewer SHALL use icons from the lucide-react library alongside section headers and insight category labels for visual affordance
5. THE Report_Viewer SHALL apply a typographic hierarchy using at least 3 distinct font sizes: section headings (minimum 20px), sub-headings (minimum 16px), and body text (minimum 14px), with headings rendered in semibold weight

### Requirement 19: Representative Reviews Section

**User Story:** As a Product Manager, I want to see notable individual reviews within the report, so that I can read actual user voices that support the AI conclusions.

#### Acceptance Criteria

1. WHEN representative reviews are available across the report insights, THE Report_Viewer SHALL render a Representative Reviews section displaying up to 10 individual review cards ordered by relevance score descending, where each card includes a Source_Badge, a 1-to-5 rating stars indicator, review date, Sentiment_Badge, review text, and keywords visually distinguished from surrounding text
2. THE Review_Card component SHALL truncate review text exceeding 300 characters and display an expand toggle that reveals the full review text when activated
3. IF no representative reviews are available in the report data, THEN THE Report_Viewer SHALL display an Empty_State component in the Representative Reviews section position
4. THE Review_Card component SHALL display keywords that appear in the review text using a background highlight style to distinguish them from non-keyword text

### Requirement 20: Report Appendix

**User Story:** As a Product Manager, I want an appendix showing how the report was generated, so that I can assess the scope and methodology of the analysis.

#### Acceptance Criteria

1. THE Report_Viewer SHALL render an Appendix section as the last section of the report, after all insight cards, displaying the following metadata fields: the AI prompt used (truncated to the first 500 characters with a clickable control to reveal the full text), the AI model name, the generation timestamp in ISO 8601 format including timezone (e.g., "2025-06-28T14:30:00Z"), a list of source names included (e.g., "Reddit, App Store, Play Store"), and the total number of reviews analyzed as an integer
2. THE Appendix section SHALL be rendered at a font size no larger than 75% of the report body text size and at a text contrast reduced relative to the body text, such that the appendix is visually subordinate to the main content
3. IF any metadata field is unavailable at render time, THEN THE Report_Viewer SHALL display the label for that field followed by a placeholder indicating the value is not available, rather than omitting the field entirely

### Requirement 21: Report List View

**User Story:** As a Product Manager, I want to see a list of all previously generated reports, so that I can navigate to and compare past analyses.

#### Acceptance Criteria

1. WHEN the Reports page is loaded and saved reports exist, THE Report_Viewer SHALL display a list of saved reports ordered by creation date descending, showing title, creation date, sources used, review count, and workflow count
2. WHEN the Reports page is loaded and no saved reports exist, THE Report_Viewer SHALL display an empty state message indicating that no reports have been generated yet
3. WHEN the user selects a report from the list, THE Report_Viewer SHALL navigate to the full report detail view displaying the report metadata and all linked insight cards
4. WHEN the user clicks the delete action on a report, THE Report_Viewer SHALL display a confirmation dialog stating the report and its linked insights will be permanently removed
5. IF the user confirms the deletion in the confirmation dialog, THEN THE Report_Viewer SHALL permanently remove the report and its linked insights and remove the entry from the displayed list
6. IF the user cancels the deletion in the confirmation dialog, THEN THE Report_Viewer SHALL close the dialog and leave the report unchanged
