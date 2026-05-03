# Requirements Document

## Introduction

This document specifies the requirements for enhancing the visual polish of the EduRisk AI Loan Officer Dashboard for the TenzorX 2026 National AI Hackathon presentation. The primary goal is to transform the dashboard into a visually stunning, high-end fintech application suitable for a professional hackathon presentation screenshot. The dashboard must appear production-ready with a focus on visual perfection over functionality, as it will be captured for Slide 7 of the presentation deck.

## Glossary

- **Dashboard**: The main portfolio view page displaying student risk analytics and KPI metrics
- **KPI_Card**: A card component displaying a single key performance indicator with value and trend
- **Risk_Badge**: A colored badge component indicating risk level (Low, Medium, High)
- **Sidebar**: The left navigation panel containing menu items with icons
- **Top_Bar**: The horizontal header bar containing search, help, and user profile elements
- **Credit_Signal_Card**: A card displaying risk driver analysis with horizontal impact bars
- **Student_Risk_Table**: A table component displaying student records with risk information
- **Action_Button**: A clickable button component for triggering operations
- **Glassmorphism**: A visual effect using subtle transparency, blur, and thin borders
- **Viewport**: The visible area of the dashboard, targeting 1280x720 resolution

## Requirements

### Requirement 1: Visual Theme and Color System

**User Story:** As a hackathon presenter, I want the dashboard to use a professional dark navy color scheme with high-contrast elements, so that it appears as a high-end fintech application in the presentation screenshot.

#### Acceptance Criteria

1. THE Dashboard SHALL use deep navy (#020617 or #0f172a) as the background color
2. THE Dashboard SHALL use card backgrounds with color #1e293b
3. THE Dashboard SHALL use primary blue accent color #3b82f6 for interactive elements
4. THE Risk_Badge SHALL use emerald color #10b981 for low risk indicators
5. THE Risk_Badge SHALL use amber color #f59e0b for medium risk indicators
6. THE Risk_Badge SHALL use rose color #ef4444 for high risk indicators
7. THE Dashboard SHALL use white color for header text with high contrast
8. THE Dashboard SHALL use muted slate color #94a3b8 for secondary text
9. THE KPI_Card SHALL apply glassmorphism effect with thin border and low opacity
10. THE KPI_Card SHALL use 12px border radius
11. THE Dashboard SHALL NOT use text-shadow effects

### Requirement 2: Typography System

**User Story:** As a hackathon presenter, I want the dashboard to use professional typography with clear hierarchy, so that text is readable and visually appealing in the screenshot.

#### Acceptance Criteria

1. THE Dashboard SHALL use Inter or DM Sans font family for all text
2. THE Dashboard SHALL use high-contrast white color for header text
3. THE Dashboard SHALL use muted slate color (#94a3b8) for secondary text
4. THE Dashboard SHALL maintain consistent font weights across similar elements

### Requirement 3: Sidebar Navigation

**User Story:** As a credit officer, I want a professional sidebar with clear navigation icons, so that I can understand the application structure at a glance.

#### Acceptance Criteria

1. THE Sidebar SHALL display a LayoutDashboard icon with "Dashboard" label in active state
2. THE Sidebar SHALL display a Users icon with "Student Database" label
3. THE Sidebar SHALL display an AlertTriangle icon with "Risk Alerts" label
4. THE Sidebar SHALL display a FileBarChart icon with "Reports" label
5. THE Sidebar SHALL display a Settings icon with "Settings" label
6. THE Sidebar SHALL use Lucide icon library for all icons
7. THE Sidebar SHALL visually indicate the active menu item

### Requirement 4: Top Bar Header

**User Story:** As a credit officer, I want a professional top bar with search and user profile, so that the dashboard appears complete and production-ready.

#### Acceptance Criteria

1. THE Top_Bar SHALL display a search input with placeholder text "Search by Student ID or Name..."
2. THE Top_Bar SHALL display a "Help" button
3. THE Top_Bar SHALL display a user profile avatar with text "Credit Officer: Arnav"
4. THE Top_Bar SHALL align search input to the left side
5. THE Top_Bar SHALL align help button and user profile to the right side

### Requirement 5: KPI Cards Display

**User Story:** As a credit officer, I want four prominent KPI cards displaying key metrics, so that I can quickly assess portfolio health.

#### Acceptance Criteria

1. THE Dashboard SHALL display four KPI_Card components in a horizontal row
2. THE KPI_Card SHALL display "Avg Placement Score" with value "74/100" and trend indicator "+2%"
3. THE KPI_Card SHALL display "Projected Portfolio CTC" with value "₹6.8L - ₹12.4L"
4. THE KPI_Card SHALL display "Early Repayment Risk" with value "Low (12.4%)"
5. THE KPI_Card SHALL display "Active Interventions" with value "48 Students"
6. THE KPI_Card SHALL display a small upward trend arrow for positive metrics
7. THE KPI_Card SHALL use large white numbers for primary values
8. THE KPI_Card SHALL use muted slate color for labels

### Requirement 6: Credit Signal Analysis Card

**User Story:** As a credit officer, I want to see risk drivers displayed as colored horizontal bars, so that I can understand which factors impact risk scores.

#### Acceptance Criteria

1. THE Dashboard SHALL display a Credit_Signal_Card component
2. THE Credit_Signal_Card SHALL have title "Credit Signal Analysis"
3. THE Credit_Signal_Card SHALL display risk drivers as horizontal bars
4. THE Credit_Signal_Card SHALL color bars based on impact magnitude
5. THE Credit_Signal_Card SHALL display driver names on the left side of bars
6. THE Credit_Signal_Card SHALL display impact values on the right side of bars

### Requirement 7: Placement Probability Chart

**User Story:** As a credit officer, I want to see placement probabilities for 3, 6, and 12 month periods as a bar chart, so that I can assess placement timeline risk.

#### Acceptance Criteria

1. THE Dashboard SHALL display a placement probability bar chart
2. THE Dashboard SHALL display bars for 3 month, 6 month, and 12 month periods
3. THE Dashboard SHALL display large white numbers on top of each bar
4. THE Dashboard SHALL use clear axis labels
5. THE Dashboard SHALL use consistent bar colors matching the theme

### Requirement 8: Student Risk Table

**User Story:** As a credit officer, I want to see a table of students with risk information and action buttons, so that I can review individual cases.

#### Acceptance Criteria

1. THE Student_Risk_Table SHALL display columns: Student Name, Course, Institute Tier, Risk Score, Flag, Action
2. THE Student_Risk_Table SHALL display realistic mock data matching presentation narrative
3. THE Student_Risk_Table SHALL display student name "Rahul Sharma" in first row
4. THE Student_Risk_Table SHALL display course "MBA" for first row
5. THE Student_Risk_Table SHALL display institute tier "Tier 1" for first row
6. THE Student_Risk_Table SHALL display risk score "82" for first row
7. THE Student_Risk_Table SHALL display a Risk_Badge with "Low Risk" for first row
8. THE Student_Risk_Table SHALL display a "Review" Action_Button in each row
9. THE Student_Risk_Table SHALL use alternating row backgrounds for readability

### Requirement 9: Action Buttons

**User Story:** As a credit officer, I want prominent action buttons for key operations, so that the dashboard appears feature-complete and professional.

#### Acceptance Criteria

1. THE Top_Bar SHALL display a "Generate RBI Audit Trail" Action_Button with primary blue styling
2. THE Top_Bar SHALL display a "Download Risk Report (PDF)" Action_Button with outline styling
3. THE Top_Bar SHALL display a "Bulk Import Applications (CSV)" Action_Button with ghost styling and upload icon
4. THE Student_Risk_Table SHALL display a "Trigger Intervention" Action_Button in each row
5. THE Action_Button SHALL use consistent padding and border radius
6. THE Action_Button SHALL display appropriate icons from Lucide library

### Requirement 10: Mock Data Consistency

**User Story:** As a hackathon presenter, I want the dashboard to display hardcoded mock data that matches the presentation narrative, so that the screenshot aligns perfectly with the slide content.

#### Acceptance Criteria

1. THE Dashboard SHALL display placement score value "74" in KPI_Card
2. THE Dashboard SHALL display salary range "₹7.2L - ₹9.8L" or "₹6.8L - ₹12.4L" in KPI_Card
3. THE Dashboard SHALL display consistent mock data across all components
4. THE Dashboard SHALL use realistic Indian names for student records
5. THE Dashboard SHALL use realistic course names (MBA, B.Tech, MCA)
6. THE Dashboard SHALL use realistic institute tiers (Tier 1, Tier 2, Tier 3)

### Requirement 11: Viewport Optimization

**User Story:** As a hackathon presenter, I want the dashboard to fit perfectly in a 1280x720 viewport, so that the screenshot captures all content without overflow or scrolling.

#### Acceptance Criteria

1. THE Dashboard SHALL fit all primary content within 1280x720 pixel viewport
2. THE Dashboard SHALL NOT display horizontal scrollbars at 1280x720 resolution
3. THE Dashboard SHALL NOT display vertical scrollbars for primary content at 1280x720 resolution
4. THE Dashboard SHALL use responsive grid layouts that adapt to viewport size
5. THE Dashboard SHALL maintain visual hierarchy at 1280x720 resolution

### Requirement 12: Component Styling Consistency

**User Story:** As a hackathon presenter, I want all components to follow consistent styling patterns, so that the dashboard appears cohesive and professionally designed.

#### Acceptance Criteria

1. THE Dashboard SHALL apply 12px border radius to all card components
2. THE Dashboard SHALL use consistent spacing between components
3. THE Dashboard SHALL use consistent padding within card components
4. THE Dashboard SHALL use consistent font sizes for similar element types
5. THE Dashboard SHALL use consistent hover states for interactive elements

### Requirement 13: Visual Effects and Polish

**User Story:** As a hackathon presenter, I want subtle visual effects that enhance the premium feel, so that the dashboard stands out in the presentation.

#### Acceptance Criteria

1. THE KPI_Card SHALL display subtle glassmorphism effect with thin border
2. THE KPI_Card SHALL use low opacity for glassmorphism effect
3. THE Action_Button SHALL display hover state with color transition
4. THE Student_Risk_Table SHALL display hover state on rows
5. THE Dashboard SHALL NOT use drop shadows on text elements
6. THE Dashboard SHALL use subtle shadows on card components for depth

### Requirement 14: Icon Integration

**User Story:** As a credit officer, I want consistent, professional icons throughout the interface, so that the dashboard appears polished and intuitive.

#### Acceptance Criteria

1. THE Dashboard SHALL use Lucide icon library for all icons
2. THE Sidebar SHALL display appropriate icons for each menu item
3. THE KPI_Card SHALL display relevant icons for each metric
4. THE Action_Button SHALL display relevant icons where appropriate
5. THE Dashboard SHALL use consistent icon sizes within similar contexts

### Requirement 15: File Updates

**User Story:** As a developer, I want to know which specific files need updates, so that I can implement the visual polish efficiently.

#### Acceptance Criteria

1. THE implementation SHALL update frontend/app/dashboard/page.tsx for overall layout and grid
2. THE implementation SHALL update frontend/components/dashboard/RiskScoreCard.tsx for KPI card styling
3. THE implementation SHALL update frontend/components/dashboard/StudentTable.tsx for table headers and badges
4. THE implementation SHALL update frontend/app/globals.css for dark navy background consistency
5. THE implementation SHALL maintain TypeScript type safety in all updated files

