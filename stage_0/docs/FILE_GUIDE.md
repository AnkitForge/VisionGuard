# Project Structure & File Guide

## File Organization

```
project IV/
├── STAGE_0_README.md              # Main Stage 0 overview
├── stage_0/
│   ├── README.md                  # Stage 0 quick reference
│   │
│   ├── html/
│   │   ├── index.html             # Home/Landing page
│   │   ├── dashboard.html         # Live monitoring dashboard
│   │   ├── alerts.html            # Alerts & incidents log
│   │   └── settings.html          # System configuration page
│   │
│   ├── css/
│   │   └── style.css              # Unified styling
│   │
│   ├── js/
│   │   └── main.js                # JavaScript functionality
│   │
│   └── docs/
│       ├── ARCHITECTURE.md        # System design & components
│       ├── REQUIREMENTS.md        # Technical specifications
│       ├── WORKFLOW.md            # Operational workflows
│       └── FILE_GUIDE.md          # This file
```

## File Descriptions

### HTML Files (stage_0/html/)

#### **index.html**
- **Purpose**: Landing/home page for the system
- **Features**:
  - Project overview and objectives
  - System status indicators
  - Quick navigation buttons
  - Feature highlights
  - Progress tracking
- **Navigation Entry**: Home

#### **dashboard.html**
- **Purpose**: Live monitoring interface
- **Features**:
  - CCTV camera feed display (4 cameras)
  - Real-time statistics
  - Activity log
  - Camera control buttons
  - System controls
- **Navigation Entry**: Dashboard

#### **alerts.html**
- **Purpose**: Alert management and incident review
- **Features**:
  - Alert statistics
  - Filter and search functionality
  - Alert table/log
  - Incident analysis panel
  - Evidence management
  - Export/download options
- **Navigation Entry**: Alerts

#### **settings.html**
- **Purpose**: System configuration and preferences
- **Features**:
  - General settings
  - Camera configuration
  - AI detection settings
  - Alert notification settings
  - Storage settings
  - System information
  - Save/Reset/Test buttons
- **Navigation Entry**: Settings

### CSS Files (stage_0/css/)

#### **style.css**
- **Purpose**: Unified styling for all pages
- **Features**:
  - Dark theme with cyan/red accents
  - Responsive design (desktop, tablet, mobile)
  - Component styling (cards, buttons, forms, tables)
  - Animations and transitions
  - Color scheme: #00d4ff (cyan), #e94560 (red), #16213e (dark blue)

### JavaScript Files (stage_0/js/)

#### **main.js**
- **Purpose**: Core client-side functionality
- **Features**:
  - Page initialization
  - Event listener setup
  - Navigation highlighting
  - Date/time updates
  - Button event handlers
  - Console logging

### Documentation Files (stage_0/docs/)

#### **ARCHITECTURE.md**
- **Purpose**: System design and technical architecture
- **Contents**:
  - Architecture layers overview
  - Component interactions
  - Technology stack
  - Data flow diagrams
  - Module dependencies
  - Performance metrics
  - Scalability considerations
  - Security architecture
  - Future enhancements

#### **REQUIREMENTS.md**
- **Purpose**: Comprehensive system requirements
- **Contents**:
  - Hardware specifications (minimum & recommended)
  - Software requirements
  - Database specifications
  - Network requirements
  - CCTV camera specifications
  - Browser requirements
  - Storage & archival needs
  - Performance benchmarks
  - Compliance standards

#### **WORKFLOW.md**
- **Purpose**: Operational and process workflows
- **Contents**:
  - Real-time monitoring workflow
  - Alert management lifecycle
  - Configuration workflow
  - Evidence management process
  - System maintenance tasks
  - Troubleshooting procedures
  - User interaction workflows
  - Error handling process

#### **FILE_GUIDE.md**
- **Purpose**: This document - file structure and navigation reference

## Quick Start Guide

### 1. **First Time Setup**
1. Extract project to: `c:\Users\546ut\OneDrive\Desktop\project IV\`
2. Read [STAGE_0_README.md](STAGE_0_README.md) for overview
3. Open `stage_0/html/index.html` in web browser (Chrome recommended)
4. Explore all pages via navigation menu

### 2. **Understanding the System**
1. Start with [ARCHITECTURE.md](stage_0/docs/ARCHITECTURE.md) for design overview
2. Read [REQUIREMENTS.md](stage_0/docs/REQUIREMENTS.md) for specifications
3. Study [WORKFLOW.md](stage_0/docs/WORKFLOW.md) for operation details

### 3. **Frontend Development**
- Modify HTML files in `stage_0/html/`
- Update styles in `stage_0/css/style.css`
- Add functionality in `stage_0/js/main.js`
- Test in web browser

### 4. **Documentation Updates**
- Update technical docs in `stage_0/docs/`
- Keep README files current
- Maintain file structure consistency

## Navigation Structure

```
index.html (Home)
├─ Dashboard
│   ├─ Camera Feeds
│   ├─ Real-time Stats
│   ├─ Activity Log
│   └─ Control Buttons
├─ Alerts
│   ├─ Alert Statistics
│   ├─ Filter & Search
│   ├─ Alert Log
│   └─ Evidence Viewer
└─ Settings
    ├─ General Settings
    ├─ Camera Configuration
    ├─ AI Detection Settings
    ├─ Alert Settings
    ├─ Storage Settings
    └─ System Information
```

## Key Features by Page

### Home (index.html)
- ✓ Project overview
- ✓ System status display
- ✓ Benefits and features list
- ✓ Technology stack info
- ✓ Quick navigation
- ✓ Progress indicator

### Dashboard (dashboard.html)
- ✓ 4 camera display grid
- ✓ Real-time statistics
- ✓ Activity monitoring
- ✓ System controls (Start/Stop/Reset)
- ✓ Camera information display

### Alerts (alerts.html)
- ✓ Alert statistics (Total, Critical, Today, Resolved)
- ✓ Advanced filtering (Date, Severity, Status)
- ✓ Alert log table
- ✓ Incident details panel
- ✓ Video evidence viewer
- ✓ Report generation buttons

### Settings (settings.html)
- ✓ General configuration
- ✓ Camera setup options
- ✓ AI model selection
- ✓ Alert method configuration
- ✓ Storage preferences
- ✓ System information display
- ✓ Configuration management buttons

## Styling System

### Color Scheme
```css
Primary Cyan:  #00d4ff
Primary Red:   #e94560
Dark Blue:     #16213e, #0f3460
Light Text:    #e0e0e0, #d0d0d0
Accent:        #874ef0 (Purple)
```

### Responsive Breakpoints
- Desktop: 1200px+
- Tablet: 768px - 1199px
- Mobile: Below 768px

### Component Types
- Status Cards
- Info Cards
- Buttons (Primary, Secondary, Tertiary)
- Forms (Input, Select, Checkbox)
- Tables
- Grids
- Panels
- Progress Bars

## Future Enhancements (Stage 1+)

### Backend Implementation
- Flask/Django API server
- Database integration
- Real CCTV camera connections
- AI model integration
- WebSocket real-time updates

### Frontend Enhancements
- React/Vue.js framework
- Real-time live streaming
- Dynamic data updates
- Advanced charting
- Video player integration
- User authentication UI

### Feature Additions
- Actual video processing
- Real AI detection
- Email/SMS integration
- Mobile app
- Cloud integration
- Advanced analytics

## File Access Workflow

```
User Opens Browser
    ↓
User Navigates to Stage 0
    ↓
Loads index.html
    ↓
CSS (style.css) Applied
    ↓
JS (main.js) Initialized
    ↓
Navigation Available
    ↓
User Clicks Menu Item
    ↓
Load new HTML page
    ↓
CSS Already Loaded (cached)
    ↓
JS Functions Available
    ↓
Page Rendered & Interactive
```

## Development Tips

1. **Testing HTML Changes**
   - Save changes
   - Refresh browser (F5 or Ctrl+R)
   - Clear cache if needed (Ctrl+Shift+Delete)

2. **Testing CSS Changes**
   - Save style.css
   - Hard refresh (Ctrl+F5)
   - Check browser console for errors

3. **Testing JS Changes**
   - Save main.js
   - Hard refresh (Ctrl+F5)
   - Open browser console (F12) to check logs

4. **Cross-Browser Testing**
   - Test in Chrome (primary)
   - Test in Firefox
   - Test in Edge
   - Test in Safari (if available)

5. **Responsive Testing**
   - Use browser DevTools (F12)
   - Toggle device toolbar
   - Test multiple screen sizes

## Documentation Maintenance

### When to Update Files
- Add new pages → Update FILE_GUIDE.md
- Change system design → Update ARCHITECTURE.md
- Add new requirements → Update REQUIREMENTS.md
- Modify workflows → Update WORKFLOW.md
- Major version change → Update README files

### Version Tracking
- All documents marked as "Stage 0"
- Last updated: February 28, 2026
- Update timestamps when changes made

## Support & Troubleshooting

### Common Issues

**Pages not loading correctly**
- Check file paths in HTML links
- Verify CSS file location
- Clear browser cache
- Try different browser

**Styling looks wrong**
- Ensure style.css is in correct folder
- Check CSS file path in HTML `<link>` tag
- Run hard refresh (Ctrl+F5)

**Navigation not working**
- Verify all HTML files exist
- Check anchor href values in navigation
- Ensure main.js is loaded

**Responsive design broken**
- Check viewport meta tag in HTML
- Verify media queries in CSS
- Test in browser DevTools responsive mode

---

**Document Status**: Stage 0 - Foundation Phase
**Last Updated**: February 28, 2026
**Version**: 1.0
