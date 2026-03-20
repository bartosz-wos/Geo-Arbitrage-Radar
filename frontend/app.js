function togglePanel(contentId, arrowId) {
  const content = document.getElementById(contentId);
  const arrow = document.getElementById(arrowId);
  if (content.classList.contains('hidden')) {
    content.classList.remove('hidden');
    arrow.innerText = '▼';
  } else {
    content.classList.add('hidden');
    arrow.innerText = '▶';
  }
}

let globalData = [];
let currentRadius = 2.0;
let currentThreshold = 20;

let showHex = true;
let showDots = true;
let showAllOffers = false;

const INITIAL_VIEW_STATE = { longitude: 21.005, latitude: 52.231, zoom: 12.5, pitch: 55, bearing: 10 };

const deckgl = new deck.DeckGL({
  container: 'map',
  initialViewState: INITIAL_VIEW_STATE,
  controller: true,
  mapStyle: 'https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json',
  layers: []
});

function getDistanceKm(lon1, lat1, lon2, lat2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2);
  return R * (2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)));
}

function getArbitrageData(point) {
  let neighborsPrices = [];
  globalData.forEach(other => {
    if (getDistanceKm(point.position[0], point.position[1], other.position[0], other.position[1]) <= currentRadius) {
      neighborsPrices.push(other.price);
    }
  });

  if (neighborsPrices.length <= 1) return { isDeal: false, discountPct: 0 };

  let avgLocalPrice = neighborsPrices.reduce((a, b) => a + b, 0) / neighborsPrices.length;
  let discount = 1.0 - (point.price / avgLocalPrice);

  return {
    isDeal: discount >= (currentThreshold / 100.0),
    discountPct: Math.round(discount * 100)
  };
}

function renderMap() {
  let deals = [];

  const processedData = globalData.map(d => {
    const arb = getArbitrageData(d);
    if (arb.isDeal) deals.push({ ...d, discountPct: arb.discountPct });
    return { ...d, ...arb };
  });

  const hexLayer = new deck.HexagonLayer({
    id: 'heatmap-layer',
    data: globalData,
    visible: showHex,
    getPosition: d => d.position,
    radius: 200,
    elevationScale: 2,
    extruded: true,
    getFillColor: [0, 255, 204, 40],
    transitions: { elevationScale: 500 }
  });

  const scatterLayer = new deck.ScatterplotLayer({
    id: 'arbitrage-layer',
    data: processedData,
    visible: showDots || showAllOffers, 
    getPosition: d => d.position,
    getFillColor: d => {
        if (showDots && d.isDeal) return [255, 0, 60, 255]; 
        if (showAllOffers) return [0, 255, 204, 80]; 
        return [0, 0, 0, 0];
    },
    getRadius: d => {
        if (showDots && d.isDeal) return 80;
        if (showAllOffers) return 80;
        return 0;
    },
    radiusMinPixels: 8,
    pickable: true,
    updateTriggers: { 
        getFillColor: [showDots, showAllOffers, currentRadius, currentThreshold],
        getRadius: [showDots, showAllOffers, currentRadius, currentThreshold]
    },

    onClick: info => {
      if (info.object && info.object.url) {
        window.open(info.object.url, '_blank');
      }
    },

    onHover: info => {
      const tooltip = document.getElementById('tooltip');
      if (info.object) {
        const pct = info.object.discountPct || 0;
        const discountColor = pct > 0 ? '#ff003c' : '#ccc';

        tooltip.innerHTML = `
          <div style="font-weight:bold; margin-bottom:5px; max-width: 250px;">${info.object.title || 'Oferta OLX'}</div>
          <div style="color:#aaa; font-size: 12px; margin-bottom:5px;">${info.object.address}</div>
          <div style="color:#fff;">${info.object.price} PLN/m²</div>
          <div style="color:${discountColor}; font-weight:bold; margin-top:5px;">
            ${pct > 0 ? 'Zniżka' : 'Powyżej średniej'}: ${pct}%
          </div>
          <div style="color:#00ffcc; font-size: 10px; margin-top:8px;">(Kliknij, aby otworzyć link)</div>
        `;
        tooltip.style.left = info.x + 'px';
        tooltip.style.top = info.y + 'px';
        tooltip.classList.remove('hidden');
      } else {
        tooltip.classList.add('hidden');
      }
    }
  });

  deckgl.setProps({ layers: [hexLayer, scatterLayer] });

  deals.sort((a, b) => b.discountPct - a.discountPct);
  const top5 = deals.slice(0, 5);

  const listHtml = top5.length === 0
    ? '<li style="color:#aaa;">No offers for given criteria</li>'
    : top5.map(d => `
        <li class="deal-item" onclick="flyTo([${d.position[0]}, ${d.position[1]}])">
          <span class="deal-address" style="font-size: 12px;">${d.title ? d.title.substring(0, 25) + '...' : d.address}</span>
          <span class="deal-stats">${d.price} PLN/m²</span>
          <span class="deal-discount">-${d.discountPct || 0}%</span>
        </li>
      `).join('');

  document.getElementById('deals-list').innerHTML = listHtml;
}

window.flyTo = function(position) {
  deckgl.setProps({
    viewState: {
      longitude: position[0], 
      latitude: position[1], 
      zoom: 15, 
      pitch: 60, 
      bearing: 0,
      transitionDuration: 1000, 
      transitionInterpolator: new deck.FlyToInterpolator()
    },
    onViewStateChange: ({viewState}) => {
      deckgl.setProps({viewState});
    }
  });
};

window.flyHome = function() {
  deckgl.setProps({
    viewState: {
      ...INITIAL_VIEW_STATE,
      transitionDuration: 1200,
      transitionInterpolator: new deck.FlyToInterpolator()
    },
    onViewStateChange: ({viewState}) => {
      deckgl.setProps({viewState});
    }
  });
};

document.getElementById('radius-slider').addEventListener('input', (e) => {
  currentRadius = parseFloat(e.target.value);
  document.getElementById('radius-val').innerText = currentRadius.toFixed(1) + ' km';
  renderMap();
});

document.getElementById('threshold-slider').addEventListener('input', (e) => {
  currentThreshold = parseInt(e.target.value);
  document.getElementById('threshold-val').innerText = currentThreshold + ' %';
  renderMap();
});

document.getElementById('toggle-hex').addEventListener('change', (e) => {
  showHex = e.target.checked;
  renderMap();
});

document.getElementById('toggle-dots').addEventListener('change', (e) => {
  showDots = e.target.checked;
  renderMap();
});

document.getElementById('toggle-all-offers').addEventListener('change', (e) => {
  showAllOffers = e.target.checked;
  renderMap();
});

fetch('data/data.json').then(r => r.json()).then(data => {
  globalData = data;
  document.getElementById('offer-count').innerText = data.length;
  renderMap();

  document.getElementById('deals-content').classList.remove('hidden');
  document.getElementById('deals-arrow').innerText = '▼';
});
