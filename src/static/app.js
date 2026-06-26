const defaultRouteRequest = {
  start: { latitude: 12.9252, longitude: 77.666125 },
  end: { latitude: 12.925253, longitude: 77.667994 },
  preferences: {
    safety: 9,
    cleanliness: 8,
    noise: 7,
    lighting: 9,
    construction: 6
  },
  data_file: 'ghost_segments.toon'
};

const heroStatus = document.getElementById('hero-status');
const ghostBtn = document.getElementById('ghost-btn');
const safetyScoreEl = document.getElementById('safety-score');
const comfortScoreEl = document.getElementById('comfort-score');
const protoTabs = [...document.querySelectorAll('.proto-tab')];
const protoPanels = [...document.querySelectorAll('.proto-panel')];

const heroMap = L.map('hero-map', {
  zoomControl: false,
  dragging: true,
  scrollWheelZoom: false,
  attributionControl: false
}).setView([12.92522, 77.6672], 16);

const phoneMap = L.map('phone-map', {
  zoomControl: false,
  dragging: false,
  scrollWheelZoom: false,
  doubleClickZoom: false,
  boxZoom: false,
  keyboard: false,
  attributionControl: false
}).setView([12.92522, 77.6672], 16);

const heroBase = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  subdomains: 'abcd',
  maxZoom: 20
}).addTo(heroMap);

const phoneBase = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  subdomains: 'abcd',
  maxZoom: 20
}).addTo(phoneMap);

const heroLayer = L.layerGroup().addTo(heroMap);
const phoneLayer = L.layerGroup().addTo(phoneMap);

function normalizeLatLonPair(pair) {
  const [first, second] = pair;
  return Math.abs(first) <= 90 ? [first, second] : [second, first];
}

function setStatus(message, error = false) {
  heroStatus.textContent = message;
  heroStatus.style.color = error ? '#ff8da2' : '#9eb2d7';
}

function animateCounter(el, target) {
  const current = Number(el.textContent) || 0;
  const diff = target - current;
  const steps = 18;
  let i = 0;

  const timer = setInterval(() => {
    i += 1;
    const next = Math.round(current + (diff * i) / steps);
    el.textContent = String(next);
    if (i >= steps) {
      clearInterval(timer);
    }
  }, 24);
}

function getSegmentAverages(route) {
  if (!route.route_coordinates || !route.route_coordinates.length) {
    return { safety: 0, cleanliness: 0, noise: 0, lighting: 0, construction: 0 };
  }

  const totals = route.route_coordinates.reduce(
    (acc, seg) => {
      acc.safety += Number(seg.metrics.safety || 0);
      acc.cleanliness += Number(seg.metrics.cleanliness || 0);
      acc.noise += Number(seg.metrics.noise || 0);
      acc.lighting += Number(seg.metrics.lighting || 0);
      acc.construction += Number(seg.metrics.construction || 0);
      return acc;
    },
    { safety: 0, cleanliness: 0, noise: 0, lighting: 0, construction: 0 }
  );

  const n = route.route_coordinates.length;
  return {
    safety: totals.safety / n,
    cleanliness: totals.cleanliness / n,
    noise: totals.noise / n,
    lighting: totals.lighting / n,
    construction: totals.construction / n
  };
}

function drawRouteOnMap(route, layerGroup, map, compact = false) {
  layerGroup.clearLayers();

  const start = normalizeLatLonPair(route.start);
  const end = normalizeLatLonPair(route.end);
  const allPoints = [start, end];

  L.circleMarker(start, {
    radius: compact ? 4 : 6,
    color: '#1de7b2',
    fillColor: '#1de7b2',
    fillOpacity: 1
  }).addTo(layerGroup);

  L.circleMarker(end, {
    radius: compact ? 4 : 6,
    color: '#ff6c88',
    fillColor: '#ff6c88',
    fillOpacity: 1
  }).addTo(layerGroup);

  (route.route_coordinates || []).forEach((segment) => {
    const line = segment.coordinates.map((point) => normalizeLatLonPair(point));
    allPoints.push(...line);

    L.polyline(line, {
      color: '#5d8fff',
      weight: compact ? 6 : 10,
      opacity: compact ? 0.35 : 0.28,
      className: 'glow-line'
    }).addTo(layerGroup);

    L.polyline(line, {
      color: '#2ea6ff',
      weight: compact ? 2 : 4,
      opacity: 0.95
    }).addTo(layerGroup);

    line.forEach((point) => {
      const risk = Math.max(0, 10 - Number(segment.metrics.safety || 0));
      const color = risk > 6 ? '#ff6c88' : risk > 3 ? '#ffcc66' : '#20e6ae';
      L.circle(point, {
        radius: compact ? 8 : 26,
        color,
        fillColor: color,
        fillOpacity: compact ? 0.15 : 0.12,
        weight: compact ? 0 : 1
      }).addTo(layerGroup);
    });
  });

  if (allPoints.length > 1) {
    map.fitBounds(allPoints, { padding: compact ? [18, 18] : [40, 40] });
  }
}

function renderFromRoute(route) {
  drawRouteOnMap(route, heroLayer, heroMap, false);
  drawRouteOnMap(route, phoneLayer, phoneMap, true);

  const avg = getSegmentAverages(route);
  const safetyScore = Math.round(((avg.safety + avg.lighting) / 20) * 100);
  const comfortScore = Math.round((((10 - avg.noise) + (10 - avg.cleanliness) + (10 - avg.construction)) / 30) * 100);

  animateCounter(safetyScoreEl, Math.max(72, safetyScore));
  animateCounter(comfortScoreEl, Math.max(68, comfortScore));
}

async function fetchRoute(payload) {
  const response = await fetch('/api/route', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  const data = await response.json();
  if (!response.ok || data.error) {
    throw new Error(data.error || 'Unable to get route');
  }

  return data;
}

async function refreshRecommendation() {
  setStatus('Computing premium safe route...');
  ghostBtn.disabled = true;

  try {
    const route = await fetchRoute(defaultRouteRequest);
    renderFromRoute(route);
    setStatus('Updated with live AI route recommendation.');
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    ghostBtn.disabled = false;
  }
}

function bindPrototypeTabs() {
  protoTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.proto;
      protoTabs.forEach((item) => item.classList.toggle('active', item === tab));
      protoPanels.forEach((panel) => {
        panel.classList.toggle('active', panel.dataset.panel === target);
      });
    });
  });
}

function drawFallbackDemo() {
  const demo = {
    start: [12.9252, 77.6661],
    end: [12.92525, 77.668],
    route_coordinates: [
      {
        coordinates: [
          [12.9252, 77.6661],
          [12.92545, 77.6669],
          [12.92568, 77.6674],
          [12.9255, 77.668]
        ],
        metrics: { safety: 8, cleanliness: 7, noise: 4, lighting: 9, construction: 2 }
      }
    ]
  };

  renderFromRoute(demo);
}

ghostBtn.addEventListener('click', refreshRecommendation);
bindPrototypeTabs();

heroMap.whenReady(() => {
  heroMap.invalidateSize();
  phoneMap.invalidateSize();
  drawFallbackDemo();
  refreshRecommendation();
});

window.addEventListener('resize', () => {
  heroMap.invalidateSize();
  phoneMap.invalidateSize();
});
