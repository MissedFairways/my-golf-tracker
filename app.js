// Global State Data Management
let shotHistory = [];
let startPosition = null;

// DOM Elements
const teeOffBtn = document.getElementById('teeOffBtn');
const atBallBtn = document.getElementById('atBallBtn');
const distanceDisplay = document.getElementById('distanceDisplay');
const clubSelect = document.getElementById('clubSelect');
const scorecardBody = document.getElementById('scorecardBody');
const averagesBody = document.getElementById('averagesBody');
const clearScorecardBtn = document.getElementById('clearScorecardBtn');

// 1. Storage Operations
function saveScorecardToStorage() {
    localStorage.setItem('golfGPS_shotHistory', JSON.stringify(shotHistory));
}

function loadScorecardFromStorage() {
    const savedData = localStorage.getItem('golfGPS_shotHistory');
    if (savedData) {
        shotHistory = JSON.parse(savedData);
        updateUI();
    }
}

// 2. Haversine Yardage Math Formula
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371e3; // Earth radius in meters
    const phi1 = lat1 * Math.PI / 180;
    const phi2 = lat2 * Math.PI / 180;
    const deltaPhi = (lat2 - lat1) * Math.PI / 180;
    const deltaLambda = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(deltaPhi/2) * Math.sin(deltaPhi/2) +
              Math.cos(phi1) * Math.cos(phi2) *
              Math.sin(deltaLambda/2) * Math.sin(deltaLambda/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    const meters = R * c;
    const yards = meters * 1.09361; // Convert meters to yards
    return Math.round(yards);
}

// 3. GPS Geolocation Handlers
teeOffBtn.addEventListener('click', () => {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            startPosition = {
                lat: position.coords.latitude,
                lon: position.coords.longitude
            };
            alert("📍 Tee position set successfully! Move to your ball and tap Click 2.");
        }, (error) => {
            alert("GPS Error: Unable to acquire start position. Ensure location services are enabled.");
        }, { enableHighAccuracy: true });
    } else {
        alert("GPS Error: Geolocation is not supported by this browser.");
    }
});

atBallBtn.addEventListener('click', () => {
    if (!startPosition) {
        alert("❌ Missing sequence! Please tap 'Click 1: Tee Off' before recording your ball position.");
        return;
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            const currentLat = position.coords.latitude;
            const currentLon = position.coords.longitude;
            
            const yardage = calculateDistance(startPosition.lat, startPosition.lon, currentLat, currentLon);
            const chosenClub = clubSelect.value;

            // Update Primary Banner Display
            distanceDisplay.textContent = `${yardage} YARDS`;

            // Commit to state arrays
            shotHistory.push({
                id: Date.now(),
                club: chosenClub,
                distance: yardage
            });

            // Save state immediately to Safari Local Storage
            saveScorecardToStorage();

            // Refresh UI tables
            updateUI();
            
            // Reset start marker for next shot tracking cycle
            startPosition = null;
        }, (error) => {
            alert("GPS Error: Unable to acquire target ball location.");
        }, { enableHighAccuracy: true });
    }
});

// 4. Interface Rendering Engine
function deleteShot(id) {
    shotHistory = shotHistory.filter(shot => shot.id !== id);
    saveScorecardToStorage();
    updateUI();
}

function updateUI() {
    // Clear dynamic content tables
    scorecardBody.innerHTML = '';
    averagesBody.innerHTML = '';

    if (shotHistory.length === 0) {
        scorecardBody.innerHTML = `<tr id="emptyScorecardRow"><td colspan="3" class="text-muted">No shots recorded yet for this round.</td></tr>`;
        averagesBody.innerHTML = `<tr id="emptyAveragesRow"><td colspan="3" class="text-muted">Track shots to calculate your averages!</td></tr>`;
        return;
    }

    // Process Shot History List
    shotHistory.forEach((shot) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${shot.club}</td>
            <td>${shot.distance} Yds</td>
            <td><button class="btn-delete" style="color:var(--danger-color); background:none; border:none; cursor:pointer;" onclick="deleteShot(${shot.id})">❌ Remove</button></td>
        `;
        scorecardBody.appendChild(row);
    });

    // Compute Metrics for Club Averages Table
    const stats = {};
    shotHistory.forEach(shot => {
        if (!stats[shot.club]) {
            stats[shot.club] = { totalDist: 0, count: 0 };
        }
        stats[shot.club].totalDist += shot.distance;
        stats[shot.club].count += 1;
    });

    Object.keys(stats).forEach(clubName => {
        const avg = Math.round(stats[clubName].totalDist / stats[clubName].count);
        const count = stats[clubName].count;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${clubName}</td>
            <td>${avg} Yds</td>
            <td>${count}</td>
        `;
        averagesBody.appendChild(row);
    });
}

// 5. Global Reset Event Listener
clearScorecardBtn.addEventListener('click', () => {
    if (confirm("⚠️ Are you sure you want to permanently clear the scorecard and reset your club averages?")) {
        shotHistory = [];
        localStorage.removeItem('golfGPS_shotHistory');
        distanceDisplay.textContent = '0 YARDS';
        updateUI();
    }
});

// 6. Application Initialization Lifecycle Trigger
document.addEventListener("DOMContentLoaded", () => {
    loadScorecardFromStorage();
});
