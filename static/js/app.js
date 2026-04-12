(function () {
    'use strict';

    var POLL_INTERVAL = 500; // ms

    var STATE_NAMES = {
        1: 'HOME',
        2: 'POSE',
        3: 'PHOTO 1',
        4: 'PHOTO 2',
        5: 'PHOTO 3',
        6: 'PHOTO 4',
        7: 'PROCESSING',
        8: 'DONE'
    };

    var stateValue = document.getElementById('state-value');
    var lastErrorLogged = false;

    function pollStatus() {
        fetch('/status')
            .then(function (res) {
                if (!res.ok) { throw new Error('HTTP ' + res.status); }
                return res.json();
            })
            .then(function (data) {
                updateUI(data);
                lastErrorLogged = false;
            })
            .catch(function (err) {
                // Log once per outage — avoid console spam during Flask restarts
                if (!lastErrorLogged) {
                    console.warn('Photobooth: lost connection to server', err);
                    lastErrorLogged = true;
                }
            });
    }

    function updateUI(data) {
        var name = STATE_NAMES[data.state] || String(data.state);
        if (stateValue) { stateValue.textContent = name; }
        // State-specific rendering is added in Phase 4
    }

    setInterval(pollStatus, POLL_INTERVAL);
    pollStatus(); // immediate first call on load
}());
