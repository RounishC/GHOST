// GHOST Route Planner - Frontend Core Logic

let map;
let datasource;
let routeLineLayer;
let altDatasource;
let altLineLayer;
let heatmapSource;
let heatmapLineLayer;
let networkSource;
let networkLineLayer;
let startMarker;
let endMarker;
let activePickerMode = null; // 'start' or 'end'
let allSegments = []; // Cache loaded segments
let currentHeatmapMetric = 'none';

// Target center of Bangalore network data
const BANGALORE_CENTER = [77.668, 12.925];

// Map Key (loaded dynamically from server config)
let AZURE_MAPS_KEY = '';

async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            const config = await response.json();
            AZURE_MAPS_KEY = config.azure_maps_key;
        }
    } catch (e) {
        console.error("Failed to load map configuration:", e);
    }
}

// Initialize when page loads
window.onload = async function () {
    initTime();
    await loadConfig();
    initMap();
    initTheme();
    loadSegmentsCache();
    
    // Set up picker click events
    document.getElementById('pick-start').onclick = () => setPickerMode('start');
    document.getElementById('pick-end').onclick = () => setPickerMode('end');
    
    // Auto-update theme check every minute
    setInterval(checkAutoTheme, 60000);
};

// Simple live clock in header
function initTime() {
    const clock = document.getElementById('system-time');
    const updateTime = () => {
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const hours = now.getHours();
        const isNight = hours >= 18 || hours < 6;
        clock.textContent = `${isNight ? '🌙 Night' : '☀️ Day'} Mode active • ${timeStr}`;
    };
    updateTime();
    setInterval(updateTime, 1000);
}

// 1. Theme Configuration
function initTheme() {
    const autoTheme = document.getElementById('auto-theme-toggle').checked;
    if (autoTheme) {
        checkAutoTheme();
    } else {
        const storedTheme = localStorage.getItem('ghost-theme') || 'night';
        setTheme(storedTheme);
    }
    
    document.getElementById('theme-manual-toggle').onclick = () => {
        // Disable auto theme when user manual toggles
        document.getElementById('auto-theme-toggle').checked = false;
        
        const isNight = document.body.classList.contains('theme-night');
        setTheme(isNight ? 'day' : 'night');
    };
}

function checkAutoTheme() {
    if (!document.getElementById('auto-theme-toggle').checked) return;
    const hour = new Date().getHours();
    const isNight = hour >= 18 || hour < 6; // 6 PM to 6 AM is night
    setTheme(isNight ? 'night' : 'day');
}

function setTheme(theme) {
    if (theme === 'night') {
        document.body.classList.remove('theme-day');
        document.body.classList.add('theme-night');
        document.querySelector('#theme-manual-toggle .theme-icon').textContent = '🌙';
        localStorage.setItem('ghost-theme', 'night');
        if (map) map.setStyle({ style: 'road_night' });
    } else {
        document.body.classList.remove('theme-night');
        document.body.classList.add('theme-day');
        document.querySelector('#theme-manual-toggle .theme-icon').textContent = '☀️';
        localStorage.setItem('ghost-theme', 'day');
        if (map) map.setStyle({ style: 'road' });
    }
}

function toggleAutoTheme() {
    const checked = document.getElementById('auto-theme-toggle').checked;
    if (checked) {
        checkAutoTheme();
    }
}

// 2. Azure Maps Setup
function initMap() {
    const isNight = document.body.classList.contains('theme-night');
    
    map = new atlas.Map('myMap', {
        center: BANGALORE_CENTER,
        zoom: 15,
        view: 'Auto',
        authOptions: {
            authType: 'subscriptionKey',
            subscriptionKey: AZURE_MAPS_KEY
        },
        style: isNight ? 'road_night' : 'road'
    });

    map.events.add('ready', function () {
        // Source for alternative routing line
        altDatasource = new atlas.source.DataSource('altRouteSource');
        map.sources.add(altDatasource);

        // Layer for drawing alternative path (light red for path we are not taking)
        altLineLayer = new atlas.layer.LineLayer(altDatasource, 'altLineLayer', {
            strokeColor: '#FF5252', // Light Red
            strokeWidth: 5,
            lineJoin: 'round',
            lineCap: 'round',
            strokeOpacity: 0.8,
            filter: ['!=', ['get', 'isConnector'], true]
        });
        map.layers.add(altLineLayer);

        // Source for routing line
        datasource = new atlas.source.DataSource('routeSource');
        map.sources.add(datasource);

        // Layer for drawing routing path (solid lines on roads)
        routeLineLayer = new atlas.layer.LineLayer(datasource, 'routeLineLayer', {
            strokeColor: '#00F3FF', // Neon Blue accent
            strokeWidth: 6,
            lineJoin: 'round',
            lineCap: 'round',
            filter: ['!=', ['get', 'isConnector'], true]
        });
        map.layers.add(routeLineLayer);

        // Layer for drawing snapped connections (dotted lines to markers)
        let connectorLineLayer = new atlas.layer.LineLayer(datasource, 'connectorLineLayer', {
            strokeColor: '#00F3FF', // Matching theme color
            strokeWidth: 4,
            strokeDashArray: [2, 2],
            lineJoin: 'round',
            lineCap: 'round',
            filter: ['==', ['get', 'isConnector'], true]
        });
        map.layers.add(connectorLineLayer);

        // Add start marker (emerald green)
        startMarker = new atlas.HtmlMarker({
            color: '#10B981',
            text: 'A',
            position: [77.666125, 12.925200],
            draggable: true
        });
        map.markers.add(startMarker);

        // Add end marker (neon cyan)
        endMarker = new atlas.HtmlMarker({
            color: '#00F3FF',
            text: 'B',
            position: [77.667994, 12.925253],
            draggable: true
        });
        map.markers.add(endMarker);

        // Listen to marker drag events to auto-fill inputs
        map.events.add('dragend', startMarker, function () {
            const pos = startMarker.getOptions().position;
            document.getElementById('start-lon').value = pos[0].toFixed(6);
            document.getElementById('start-lat').value = pos[1].toFixed(6);
        });

        map.events.add('dragend', endMarker, function () {
            const pos = endMarker.getOptions().position;
            document.getElementById('end-lon').value = pos[0].toFixed(6);
            document.getElementById('end-lat').value = pos[1].toFixed(6);
        });

        // Heatmap Source & Layer
        heatmapSource = new atlas.source.DataSource('heatmapSource');
        map.sources.add(heatmapSource);

        heatmapLineLayer = new atlas.layer.LineLayer(heatmapSource, 'heatmapLineLayer', {
            strokeWidth: 4,
            lineJoin: 'round',
            lineCap: 'round',
            strokeOpacity: 0.6,
            visible: false
        });
        map.layers.add(heatmapLineLayer);

        // Network Source & Layer (Displays all possible routes in area using thin dotted lines)
        networkSource = new atlas.source.DataSource('networkSource');
        map.sources.add(networkSource);

        networkLineLayer = new atlas.layer.LineLayer(networkSource, 'networkLineLayer', {
            strokeColor: '#718096', // Mid-gray for good contrast
            strokeWidth: 2,
            strokeDashArray: [2, 3], // Dotted line style
            strokeOpacity: 0.5,
            lineJoin: 'round',
            lineCap: 'round'
        });
        map.layers.add(networkLineLayer);

        // Populate the background network lines once layers are ready
        populateBackgroundNetwork();

        // Map click event for coordinate selection
        map.events.add('click', function (e) {
            if (!activePickerMode) return;

            const lon = e.position[0];
            const lat = e.position[1];
            
            // Snap to nearest segment node to guarantee route calculation succeeds
            const snapped = snapToNearestNode(lon, lat);
            const targetLon = snapped ? snapped[0] : lon;
            const targetLat = snapped ? snapped[1] : lat;

            if (activePickerMode === 'start') {
                document.getElementById('start-lon').value = targetLon.toFixed(6);
                document.getElementById('start-lat').value = targetLat.toFixed(6);
                startMarker.setOptions({ position: [targetLon, targetLat] });
            } else if (activePickerMode === 'end') {
                document.getElementById('end-lon').value = targetLon.toFixed(6);
                document.getElementById('end-lat').value = targetLat.toFixed(6);
                endMarker.setOptions({ position: [targetLon, targetLat] });
            }

            resetPickerMode();
        });
    });
}

// Snapping algorithm to find the closest segment node
function snapToNearestNode(lon, lat) {
    if (allSegments.length === 0) return null;
    let minDistance = Infinity;
    let nearestNode = null;

    allSegments.forEach(seg => {
        // Check start and end of segment
        const start = seg.coordinates[0];
        const end = seg.coordinates[seg.coordinates.length - 1];
        
        const distStart = Math.hypot(start[0] - lon, start[1] - lat);
        const distEnd = Math.hypot(end[0] - lon, end[1] - lat);

        if (distStart < minDistance) {
            minDistance = distStart;
            nearestNode = start;
        }
        if (distEnd < minDistance) {
            minDistance = distEnd;
            nearestNode = end;
        }
    });

    // Snapping radius of roughly 300m
    if (minDistance < 0.003) {
        return nearestNode;
    }
    return null;
}

// 3. Tab Management
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Find matching button text or target directly
    const buttons = document.querySelectorAll('.tab-btn');
    if (tabId === 'plan') buttons[0].classList.add('active');
    else if (tabId === 'heatmap') buttons[1].classList.add('active');
    else if (tabId === 'settings') buttons[2].classList.add('active');

    document.getElementById(`tab-${tabId}`).classList.add('active');
}

// Picker Mode Activation
function setPickerMode(mode) {
    resetPickerMode();
    activePickerMode = mode;
    const btn = document.getElementById(`pick-${mode}`);
    btn.classList.add('active');
    btn.textContent = '👆 Click Map';
}

function resetPickerMode() {
    activePickerMode = null;
    document.getElementById('pick-start').classList.remove('active');
    document.getElementById('pick-start').textContent = '📍';
    document.getElementById('pick-end').classList.remove('active');
    document.getElementById('pick-end').textContent = '🎯';
}

// Update value displays for sliders
function updateVal(sliderName) {
    const val = document.getElementById(`pref-${sliderName}`).value;
    document.getElementById(`val-${sliderName}`).textContent = `${val}/10`;
}

// Pre-defined preferences profiles
function applyProfile(profile) {
    if (profile === 'grandma') {
        setSliderValues(10, 2, 2, 9, 1); // high safety, low dust target, low noise, high light, low construction
    } else if (profile === 'commuter') {
        setSliderValues(7, 5, 5, 7, 5); // balanced
    } else if (profile === 'runner') {
        setSliderValues(5, 1, 1, 6, 4); // super low dust, quiet
    }
    switchTab('plan');
}

function setSliderValues(safety, dust, noise, lighting, construction) {
    document.getElementById('pref-safety').value = safety;
    document.getElementById('pref-dust').value = dust;
    document.getElementById('pref-noise').value = noise;
    document.getElementById('pref-lighting').value = lighting;
    document.getElementById('pref-construction').value = construction;
    
    updateVal('safety');
    updateVal('dust');
    updateVal('noise');
    updateVal('lighting');
    updateVal('construction');
}

// Cache segment data for snap routing and heatmaps
async function loadSegmentsCache() {
    try {
        const response = await fetch('/api/segments');
        if (response.ok) {
            allSegments = await response.json();
            console.log(`Loaded ${allSegments.length} segments into client cache`);
            populateBackgroundNetwork();
        }
    } catch (e) {
        console.error("Failed to load segment cache:", e);
    }
}

// Populate background network lines
function populateBackgroundNetwork() {
    if (!networkSource || allSegments.length === 0) return;
    networkSource.clear();
    const features = [];
    allSegments.forEach(seg => {
        features.push(new atlas.data.Feature(
            new atlas.data.LineString(seg.coordinates),
            { road_name: seg.road_name }
        ));
    });
    networkSource.add(features);
    console.log(`Successfully populated background network with ${features.length} segments`);
}

// 4. Heatmap Rendering Engine
function setHeatmapMode(metric) {
    currentHeatmapMetric = metric;
    
    // Update button states
    document.querySelectorAll('.heatmap-opt').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`heatmap-${metric}`).classList.add('active');

    // Clear existing data
    if (heatmapSource) {
        heatmapSource.clear();
    }

    if (metric === 'none') {
        document.getElementById('heatmap-legend').style.display = 'none';
        if (heatmapLineLayer) {
            heatmapLineLayer.setOptions({ visible: false });
        }
        return;
    }

    document.getElementById('heatmap-legend').style.display = 'block';

    // Set scale legend labels
    const lowLabel = document.getElementById('legend-low');
    const highLabel = document.getElementById('legend-high');

    if (metric === 'safety') {
        lowLabel.textContent = 'Low crime (Safe)';
        highLabel.textContent = 'High crime';
    } else if (metric === 'cleanliness') {
        lowLabel.textContent = 'Clean air (Low dust)';
        highLabel.textContent = 'High dust';
    } else if (metric === 'noise') {
        lowLabel.textContent = 'Quiet';
        highLabel.textContent = 'Loud';
    } else if (metric === 'lighting') {
        lowLabel.textContent = 'Dark';
        highLabel.textContent = 'Bright';
    } else if (metric === 'construction') {
        lowLabel.textContent = 'No work';
        highLabel.textContent = 'Major construction';
    }

    // Populate coordinates with metric property
    const features = [];
    allSegments.forEach(seg => {
        let val = 0;
        if (metric === 'safety') val = seg.crime_score;
        else if (metric === 'cleanliness') val = seg.dust_level;
        else if (metric === 'noise') val = seg.noise_level;
        else if (metric === 'lighting') val = seg.lighting; // Note: lighting higher is better, we invert color rendering below
        else if (metric === 'construction') val = seg.construction;

        features.push(new atlas.data.Feature(
            new atlas.data.LineString(seg.coordinates),
            {
                metric_value: val,
                road_name: seg.road_name,
                highway_type: seg.highway_type
            }
        ));
    });

    if (heatmapSource) {
        heatmapSource.add(features);
    }

    // Dynamic coloring based on metric scale
    let colorExpression;
    if (metric === 'lighting') {
        // High lighting is good (green), low lighting is bad (red)
        colorExpression = [
            'interpolate',
            ['linear'],
            ['get', 'metric_value'],
            0, '#ef4444', // Dark = Red
            5, '#f59e0b', // Moderate = Orange
            10, '#10b981' // Bright = Green
        ];
    } else {
        // High crime, dust, noise, construction is bad (red), low is good (green)
        colorExpression = [
            'interpolate',
            ['linear'],
            ['get', 'metric_value'],
            0, '#10b981', // Good = Green
            5, '#f59e0b', // Moderate = Orange
            10, '#ef4444' // Bad = Red
        ];
    }

    if (heatmapLineLayer) {
        heatmapLineLayer.setOptions({
            strokeColor: colorExpression,
            visible: true
        });
    }
}

// 5. Helper Function to crop route segments to closest points
function cropRouteSegments(routeCoordinates, startLon, startLat, endLon, endLat) {
    let croppedRouteCoordinates = [];
    if (!routeCoordinates || routeCoordinates.length === 0) return croppedRouteCoordinates;

    if (routeCoordinates.length === 1) {
        const seg = routeCoordinates[0];
        const coords = seg.coordinates;
        
        let startIdx = 0, minS = Infinity;
        for (let i = 0; i < coords.length; i++) {
            let d = Math.hypot(coords[i][0] - startLon, coords[i][1] - startLat);
            if (d < minS) { minS = d; startIdx = i; }
        }
        
        let endIdx = 0, minE = Infinity;
        for (let i = 0; i < coords.length; i++) {
            let d = Math.hypot(coords[i][0] - endLon, coords[i][1] - endLat);
            if (d < minE) { minE = d; endIdx = i; }
        }
        
        let segmentCoords = [];
        if (startIdx <= endIdx) {
            segmentCoords = coords.slice(startIdx, endIdx + 1);
        } else {
            segmentCoords = coords.slice(endIdx, startIdx + 1).reverse();
        }
        croppedRouteCoordinates.push(segmentCoords);
    } else {
        for (let idx = 0; idx < routeCoordinates.length; idx++) {
            const seg = routeCoordinates[idx];
            const coords = seg.coordinates;
            
            if (idx === 0) {
                let startIdx = 0, minS = Infinity;
                for (let i = 0; i < coords.length; i++) {
                    let d = Math.hypot(coords[i][0] - startLon, coords[i][1] - startLat);
                    if (d < minS) { minS = d; startIdx = i; }
                }
                croppedRouteCoordinates.push(coords.slice(startIdx));
            } else if (idx === routeCoordinates.length - 1) {
                let endIdx = 0, minE = Infinity;
                for (let i = 0; i < coords.length; i++) {
                    let d = Math.hypot(coords[i][0] - endLon, coords[i][1] - endLat);
                    if (d < minE) { minE = d; endIdx = i; }
                }
                croppedRouteCoordinates.push(coords.slice(0, endIdx + 1));
            } else {
                croppedRouteCoordinates.push(coords);
            }
        }
    }
    return croppedRouteCoordinates;
}

// 6. Fetch Optimal Route from Backend
async function fetchRoute() {
    const startLon = parseFloat(document.getElementById('start-lon').value);
    const startLat = parseFloat(document.getElementById('start-lat').value);
    const endLon = parseFloat(document.getElementById('end-lon').value);
    const endLat = parseFloat(document.getElementById('end-lat').value);

    // Read preferences
    const safety = parseInt(document.getElementById('pref-safety').value);
    const dust_level = parseInt(document.getElementById('pref-dust').value);
    const noise_level = parseInt(document.getElementById('pref-noise').value);
    const lighting = parseInt(document.getElementById('pref-lighting').value);
    const construction = parseInt(document.getElementById('pref-construction').value);

    // Show loading spinner
    const spinner = document.getElementById('loading-overlay');
    spinner.style.display = 'flex';

    // Position markers in case user typed them in
    startMarker.setOptions({ position: [startLon, startLat] });
    endMarker.setOptions({ position: [endLon, endLat] });

    try {
        const response = await fetch('/api/route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start: { longitude: startLon, latitude: startLat },
                end: { longitude: endLon, latitude: endLat },
                preferences: {
                    safety: safety,
                    dust_level: dust_level,
                    noise_level: noise_level,
                    lighting: lighting,
                    construction: construction
                }
            })
        });

        const data = await response.json();
        spinner.style.display = 'none';

        if (data.error) {
            alert(`Routing Error: ${data.error}`);
            return;
        }

        // Draw Route Line
        datasource.clear();
        if (typeof altDatasource !== 'undefined' && altDatasource) {
            altDatasource.clear();
        }
        
        const allCoords = [];
        let croppedRouteCoordinates = [];
        
        if (data.route_coordinates && data.route_coordinates.length > 0) {
            croppedRouteCoordinates = cropRouteSegments(data.route_coordinates, startLon, startLat, endLon, endLat);
            
            // 1. Draw solid line features for each cropped segment
            croppedRouteCoordinates.forEach(coords => {
                if (coords.length > 0) {
                    datasource.add(new atlas.data.Feature(
                        new atlas.data.LineString(coords),
                        { isConnector: false }
                    ));
                    coords.forEach(coord => {
                        allCoords.push(coord);
                    });
                }
            });

            // 2. Draw connector lines from markers to snapped endpoint locations
            const routeStart = croppedRouteCoordinates[0][0];
            const routeEnd = croppedRouteCoordinates[croppedRouteCoordinates.length - 1][croppedRouteCoordinates[croppedRouteCoordinates.length - 1].length - 1];
            
            // Marker A Connector (Dotted)
            datasource.add(new atlas.data.Feature(
                new atlas.data.LineString([[startLon, startLat], routeStart]),
                { isConnector: true }
            ));
            
            // Marker B Connector (Dotted)
            datasource.add(new atlas.data.Feature(
                new atlas.data.LineString([routeEnd, [endLon, endLat]]),
                { isConnector: true }
            ));

            allCoords.push([startLon, startLat]);
            allCoords.push([endLon, endLat]);
        }

        // 3. Draw Alternative Route Line (Light Red)
        if (data.alternative_route_coordinates && data.alternative_route_coordinates.length > 0 && typeof altDatasource !== 'undefined' && altDatasource) {
            let croppedAltCoordinates = cropRouteSegments(data.alternative_route_coordinates, startLon, startLat, endLon, endLat);
            
            croppedAltCoordinates.forEach(coords => {
                if (coords.length > 0) {
                    altDatasource.add(new atlas.data.Feature(
                        new atlas.data.LineString(coords),
                        { isConnector: false }
                    ));
                    coords.forEach(coord => {
                        allCoords.push(coord);
                    });
                }
            });
        }

        if (allCoords.length > 0) {
            // Adjust camera to fit route and markers
            const bbox = atlas.data.BoundingBox.fromPositions(allCoords);
            map.setCamera({
                bounds: bbox,
                padding: 80
            });
        }

        // Render details cards
        renderResults(data, safety, dust_level, noise_level, lighting, construction);

    } catch (e) {
        spinner.style.display = 'none';
        alert(`Failed to fetch route: ${e}`);
    }
}

// Render route analysis details in UI
function renderResults(data, safety, dust, noise, lighting, construction) {
    document.getElementById('results-card').style.display = 'block';
    
    // Distance
    document.getElementById('ghost-dist').textContent = `${data.total_distance_km} km`;
    
    // Quality scoring
    const safetyScore = data.overall_quality; // Overall quality average
    document.getElementById('safety-score-bar').style.width = `${safetyScore * 10}%`;
    document.getElementById('safety-score-txt').textContent = `${safetyScore.toFixed(1)}/10`;

    // AI Reasoning
    const reasoningContainer = document.getElementById('ai-reasoning-body');
    // Format bold text
    let formattedReasoning = data.ai_reasoning.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    reasoningContainer.innerHTML = formattedReasoning;

    // Highlights
    const highlightsContainer = document.getElementById('ai-highlights-body');
    highlightsContainer.innerHTML = '';
    data.highlights.forEach(hl => {
        const div = document.createElement('div');
        div.className = 'highlight-item';
        div.textContent = hl;
        highlightsContainer.appendChild(div);
    });

    // Dynamic Grandma Advice Generator (Thematic Grandma Experience)
    const grandmaBox = document.getElementById('grandma-advice-text');
    grandmaBox.innerHTML = generateGrandmaAdvice(data, safety, dust, noise, lighting, construction);
}

// Generate dynamic Grandma Advice based on actual route metrics and user choices
function generateGrandmaAdvice(data, safety, dust, noise, lighting, construction) {
    let advice = "";
    
    // Find the average segment details
    let avgLighting = 0;
    let avgDust = 0;
    let avgNoise = 0;
    let avgCrime = 0;
    let avgConstruction = 0;
    let totalSegments = data.route_coordinates.length;

    data.route_coordinates.forEach(seg => {
        avgLighting += seg.metrics.lighting;
        // Handle database names differences
        avgDust += seg.metrics.cleanliness || 5; 
        avgNoise += seg.metrics.noise || 5;
        avgCrime += seg.metrics.safety || 5;
        avgConstruction += seg.metrics.construction || 0;
    });

    avgLighting /= totalSegments;
    avgDust /= totalSegments;
    avgNoise /= totalSegments;
    avgCrime /= totalSegments;
    avgConstruction /= totalSegments;

    // Intro advice
    advice += `"Oh sweetie, I've checked the road for you. `;

    // 1. Safety / Crime advice
    if (avgCrime <= 3) {
        advice += `It's a very peaceful neighborhood. I don't see any bad elements around, so you can walk without looking over your shoulder. `;
    } else {
        advice += `Some parts have had a bit of rowdiness lately. Keep your purse close, look straight ahead, and don't stop for anyone! `;
    }

    // 2. Lighting advice
    if (avgLighting >= 7) {
        advice += `The street lamps are nice and bright (avg lighting score of ${avgLighting.toFixed(1)}/10), which makes my old eyes happy. `;
    } else {
        advice += `It's dreadfully dark on some of these segments! Turn your phone flashlight on, watch out for potholes, and please stay alert. `;
    }

    // 3. Dust / Cleanliness advice
    if (avgDust >= 6) {
        advice += `It's quite dusty out there, dear. Wrap a scarf around your mouth so you don't keep coughing! `;
    }

    // 4. Construction advice
    if (avgConstruction >= 4) {
        advice += `Watch your step on the sidewalk, there's construction equipment lying around. You don't want to trip and scuff your knees! `;
    }

    // Outro
    advice += `Make sure to text me as soon as you arrive, okay? Wear a sweater, it gets drafty!"`;

    return advice;
}
