# 🎨 Frontend Development Prompt for GHOST Route Planner

## Backend API Ready ✅

Your backend is running on `http://localhost:5000` and returns:
- **Start/End coordinates** - Exact GPS points
- **Route coordinates** - Array of [longitude, latitude] pairs for each street
- **Street names** - Human-readable street names
- **Distance & metrics** - For each segment
- **AI reasoning** - Explanation of route choice

---

## Frontend Development Prompt

### Task
Build an interactive web frontend for the GHOST Route Planner that:
1. Accepts user input for start/end locations
2. Allows users to set preferences (safety, cleanliness, noise, lighting, construction)
3. Calls the backend API at `POST http://localhost:5000/api/route`
4. Displays the optimal route on an interactive map with:
   - Start point marker (green)
   - End point marker (red)
   - Route path highlighted in blue
   - Street names labeled on the route
   - Quality metrics visualization
5. Shows AI-generated reasoning for why this route was selected
6. Responsive design works on mobile and desktop

### API Response Format

The backend returns a JSON response with:
```json
{
  "success": true,
  "start": [77.666125, 12.925200],
  "end": [77.667994, 12.925253],
  "streets": ["Genesis Parking Road"],
  "route_coordinates": [
    {
      "street": "Genesis Parking Road",
      "type": "residential",
      "distance_meters": 184.5,
      "coordinates": [[77.6680519, 12.9256894], [77.6677478, 12.925695], [77.6663502, 12.925726]],
      "metrics": {
        "safety": 9,
        "cleanliness": 3,
        "noise": 3,
        "lighting": 2,
        "construction": 0
      }
    }
  ],
  "total_distance_km": 0.18,
  "total_distance_meters": 184.5,
  "overall_quality": 3.4,
  "ai_reasoning": "**Efficient Route**: The recommended path...",
  "highlights": ["✓ Safest segment: Genesis Parking Road", "⚠️ Higher crime area..."]
}
```

### Tech Stack Recommendations

**Option 1: React + Leaflet (Recommended)**
- **React** - UI framework
- **Leaflet** - Lightweight map library
- **react-leaflet** - React bindings for Leaflet
- **Tailwind CSS** - Styling

**Option 2: Vue + Mapbox GL**
- **Vue 3** - UI framework
- **Mapbox GL** - Feature-rich maps
- **Vite** - Build tool

**Option 3: Vanilla JS + Leaflet**
- **Leaflet** - Map library
- **Fetch API** - HTTP requests
- **HTML5 Canvas** - Animations (optional)

### Key Features to Implement

#### 1. Input Form
```
┌─────────────────────────────────┐
│ Start Location                  │
│ [Latitude] [Longitude]          │
│                                 │
│ End Location                    │
│ [Latitude] [Longitude]          │
│                                 │
│ Safety: [Slider 1-10]           │
│ Cleanliness: [Slider 1-10]      │
│ Noise: [Slider 1-10]            │
│ Lighting: [Slider 1-10]         │
│ Construction: [Slider 1-10]     │
│                                 │
│ [Find Route] [Reset]            │
└─────────────────────────────────┘
```

#### 2. Map Display
- Use Leaflet or Mapbox GL
- Plot start point (green marker)
- Plot end point (red marker)
- Draw polyline for route using coordinate arrays
- Show street names on hover
- Add zoom controls

#### 3. Route Details Panel
```
Route: Genesis Parking Road
Distance: 0.18 km (184.5 m)
Quality: 3.4/10
Streets: Genesis Parking Road

Metrics:
  Safety: 9/10 ████████░░
  Cleanliness: 3/10 ███░░░░░░░
  Noise: 3/10 ███░░░░░░░
  Lighting: 2/10 ██░░░░░░░░

💡 Why this route?
**Efficient Route**: The recommended path covers only 184 meters...
```

#### 4. Error Handling
- Show error messages if coordinates are invalid
- Handle API timeouts
- Show loading state while fetching

---

## Sample React Component Structure

```
src/
├── components/
│   ├── SearchForm.jsx        - Input form for coordinates & preferences
│   ├── MapDisplay.jsx        - Leaflet map component
│   ├── RouteDetails.jsx      - Display route info & metrics
│   ├── AIReasoning.jsx       - Show AI explanation
│   └── LoadingSpinner.jsx    - Loading state
├── services/
│   └── api.js               - API calls to backend
├── hooks/
│   └── useRoute.js          - Custom hook for route logic
├── App.jsx
└── index.css
```

---

## API Integration Example (React)

```jsx
// services/api.js
export async function getRoute(start, end, preferences) {
  const response = await fetch('http://localhost:5000/api/route', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      start: { longitude: start[0], latitude: start[1] },
      end: { longitude: end[0], latitude: end[1] },
      preferences,
      data_file: 'ghost_segments.toon'
    })
  });
  
  if (!response.ok) throw new Error('Route not found');
  return response.json();
}

// MapDisplay.jsx
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';

export function MapDisplay({ route }) {
  if (!route) return <div>No route</div>;
  
  const polylines = route.route_coordinates.map(segment => (
    <Polyline
      key={segment.street}
      positions={segment.coordinates.map(([lon, lat]) => [lat, lon])}
      color="blue"
      weight={3}
      opacity={0.7}
    />
  ));
  
  const [startLat, startLon] = route.start;
  const [endLat, endLon] = route.end;
  
  return (
    <MapContainer center={[startLat, startLon]} zoom={17} style={{height: '500px'}}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Marker position={[startLat, startLon]}>
        <Popup>Start</Popup>
      </Marker>
      <Marker position={[endLat, endLon]}>
        <Popup>End</Popup>
      </Marker>
      {polylines}
    </MapContainer>
  );
}
```

---

## Deployment

### Backend
```bash
cd /Users/jiya/Downloads/GHOST
pip install flask flask-cors
python3 src/api_server.py
```

### Frontend (React + Vite)
```bash
npm create vite@latest ghost-route-frontend -- --template react
cd ghost-route-frontend
npm install leaflet react-leaflet
npm run dev
```

---

## Testing Checklist

- [ ] Form accepts coordinates
- [ ] Sliders for preferences work (0-10 scale)
- [ ] "Find Route" button calls API
- [ ] Map displays with markers
- [ ] Route polyline drawn correctly
- [ ] Street names visible
- [ ] Distance shown correctly
- [ ] AI reasoning displayed
- [ ] Responsive on mobile
- [ ] Error handling works

---

## Map Libraries Comparison

| Feature | Leaflet | Mapbox GL | Google Maps |
|---------|---------|-----------|------------|
| License | Open Source | Freemium | Proprietary |
| Cost | Free | Free tier | Paid |
| Learning Curve | Easy | Medium | Easy |
| Performance | Good | Excellent | Good |
| Mobile | Good | Excellent | Good |

**Recommendation**: Use **Leaflet** for simplicity, **Mapbox GL** for advanced features.

---

## Next Steps

1. **Install dependencies** for backend API
2. **Start API server**: `python3 src/api_server.py`
3. **Build frontend** with your preferred framework
4. **Test API calls** with sample coordinates
5. **Deploy** to a hosting service (Vercel, Netlify, etc.)

The backend is ready. Time to build the frontend! 🚀
