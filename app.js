// Global App Variables
let shotHistory = [];
let teeCoordinates = null;

// Target Elements
const btnClick1 = document.getElementById('btnClick1');
const btnClick2 = document.getElementById('btnClick2');
const distanceOutput = document.getElementById('distanceOutput');
const clubSelect = document.getElementById('clubSelect');
const statusMessage = document.getElementById('statusMessage');
const scorecardBody = document.getElementById('scorecardBody');
const averagesBody = document.getElementById('averagesBody');
const btnClearAll = document.getElementById('btnClearAll');

// 1. Data Storage Cycle
function saveScorecardToStorage() {
    localStorage.setItem('golf_shotHistory_v1', JSON.stringify(shotHistory));
}

function loadScorecardFromStorage() {
    const data = localStorage.getItem('golf_shotHistory_v1');
    if (data) {
        shotHistory = JSON.parse(data);
        renderTables();
    }
}

// 2. Exact GPS Mathematical Conversion Formula
function calculateYards(lat1, lon1, lat2, lon2) {
    const earthRadiusMeters = 6371000;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distanceMeters = earthRadiusMeters * c;
    
    return Math.round(distanceMeters * 1.09361);
}

// 3. Coordinate Capture Engines
btnClick1.addEventListener('click', () => {
    statusMessage.textContent = "⏳ Accessing iPhone GPS coordinates...";
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((pos) => {
            teeCoordinates = {
                latitude: pos.coords.latitude,
                longitude: pos.coords.longitude
            };
            statusMessage.textContent = "🎯 Click 1 Saved! Walk down the fairway to your ball and tap Click 2.";
        }, (err) => {
            statusMessage.textContent = "❌ GPS Lock Failure. Check Safari privacy configurations.";
        }, { enableHighAccuracy: true, timeout: 10000 });
    } else {
        statusMessage.textContent = "❌ Geolocation unsupported on this device.";
    }
});

btnClick2.addEventListener('click', () => {
    if (!teeCoordinates) {
        statusMessage.textContent = "⚠️ Register your Tee location first via Click 1!";
        return;
    }
    
    statusMessage.textContent = "⏳ Measuring landing spot...";
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((pos) => {
            const calculatedDistance = calculateYards(
                teeCoordinates.latitude,
                teeCoordinates.longitude,
                pos.coords.latitude,
                pos.coords.longitude
            );
            
            const currentClub = clubSelect.value;
            distanceOutput.textContent = `${calculatedDistance} YARDS`;
            
            // Add entry to state array
            shotHistory.push({
                timestampId: Date.now(),
                club: currentClub,
                yards: calculatedDistance
            });
            
            // Update storage immediately
            saveScorecardToStorage();
            
            // Refresh visuals
            renderTables();
            
            statusMessage.textContent = `✅ Recorded ${calculatedDistance} yds with ${currentClub}. Ready for next tee box.`;
            teeCoordinates = null; // Flush coordinate anchor
        }, (err) => {
            statusMessage.textContent = "❌ Target position lock failed.";
        }, { enableHighAccuracy: true, timeout: 10000 });
    }
});

// 4. Scorecard Table Generator
window.removeShot = function(timestampId) {
    shotHistory = shotHistory.filter(shot => shot.timestampId !== timestampId);
    saveScorecardToStorage();
    renderTables();
};

function renderTables() {
    scorecardBody.innerHTML = '';
    averagesBody.innerHTML = '';
    
    if (shotHistory.length === 0) {
        scorecardBody.innerHTML = `<tr><td colspan="3" class="empty-text">No shots recorded yet for this round.</td></tr>`;
        averagesBody.innerHTML = `<tr><td colspan="3" class="empty-text">Track shots to calculate your averages!</td></tr>`;
        return;
    }
    
    // Sort shots chronologically (newest at top)
    const reversedHistory = [...shotHistory].reverse();
    
    reversedHistory.forEach(shot => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${shot.club}</strong></td>
            <td>${shot.yards} Yds</td>
            <td><button style="padding:4px 8px; font-size:0.8rem; background-color:#fed7d7; color:#c53030; border-radius:4px;" onclick="window.removeShot(${shot.timestampId})">Remove</button></td>
        `;
        scorecardBody.appendChild(tr);
    });
    
    // Compute Club Statistics
    const metrics = {};
    shotHistory.forEach(shot => {
        if (!metrics[shot.club]) {
            metrics[shot.club] = { aggregate: 0, count: 0 };
        }
        metrics[shot.club].aggregate += shot.yards;
        metrics[shot.club].count++;
    });
    
    Object.keys(metrics).forEach(club => {
        const averageValue = Math.round(metrics[club].aggregate / metrics[club].count);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${club}</strong></td>
            <td>${averageValue} Yds</td>
            <td>${metrics[club].count}</td>
        `;
        averagesBody.appendChild(tr);
    });
}

// 5. Global Table Wipe Operation
btnClearAll.addEventListener('click', () => {
    if (confirm("🚨 Wipe entire round history and reset your club metrics?")) {
        shotHistory = [];
        localStorage.removeItem('golf_shotHistory_v1');
        distanceOutput.textContent = '0 YARDS';
        statusMessage.textContent = '⛳ Stand on the tee box and tap Click 1.';
        renderTables();
    }
});

// 6. Complete Initialization Sequence Hook
document.addEventListener("DOMContentLoaded", () => {
    loadScorecardFromStorage();
});

