(function () {
    'use strict';

    var POLL_INTERVAL = 300; // ms — fast enough for snappy state transitions

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

    // ---------------------------------------------------------------------------
    // Element refs
    // ---------------------------------------------------------------------------
    var stateValue  = document.getElementById('state-value');
    var splashEl    = document.getElementById('splash');
    var contentEl   = document.getElementById('content');
    var llamaDancer = document.getElementById('llama-dancer');

    // ---------------------------------------------------------------------------
    // Llama animation — controlled entirely by CSS via the 'animating' class.
    // No JS timers: the @keyframes animation runs on the compositor thread,
    // isolated from poll-driven event loop pressure.
    // ---------------------------------------------------------------------------
    function startLlama() {
        llamaDancer.classList.add('animating');
    }

    function stopLlama() {
        llamaDancer.classList.remove('animating');
    }

    // ---------------------------------------------------------------------------
    // Spacebar trigger — active only in state 1
    // ---------------------------------------------------------------------------
    var currentState = null;

    document.addEventListener('keydown', function (e) {
        if (e.code !== 'Space') return;
        if (currentState !== 1) return;
        e.preventDefault();
        fetch('/trigger', { method: 'POST' })
            .catch(function (err) {
                console.warn('Photobooth: trigger failed', err);
            });
    });

    // ---------------------------------------------------------------------------
    // State entry — called once per state transition
    // ---------------------------------------------------------------------------
    function onStateEnter(state, data) {
        // Splash background
        splashEl.style.backgroundImage =
            'url(/static/splash/splash_' + state + '.png)';

        // Llama dancer visibility
        if (state === 1) {
            llamaDancer.classList.remove('hidden');
            startLlama();
        } else {
            llamaDancer.classList.add('hidden');
            stopLlama();
        }

        // State-specific content
        switch (state) {
            case 1:
                contentEl.innerHTML =
                    '<div class="state-heading">PUSH THE BUTTON</div>';
                break;

            case 2:
                contentEl.innerHTML =
                    '<div class="state-heading">STRIKE A POSE</div>';
                break;

            case 3:
            case 4:
            case 5:
            case 6:
                contentEl.innerHTML =
                    '<div class="countdown-numeral">' + (state - 2) + '</div>';
                break;

            case 7:
                contentEl.innerHTML =
                    '<div class="state-heading">PROCESSING&hellip;</div>';
                break;

            case 8:
                // All 4 photos displayed simultaneously in a 2×2 grid.
                // Eliminates the server/client timing race that caused
                // 2–4 photos to appear depending on Pi load.
                var photos = data.photos || [];
                var html = '<div class="review-grid">';
                for (var i = 0; i < photos.length; i++) {
                    html += '<img class="review-photo" src="' + photos[i] +
                            '" alt="Photo ' + (i + 1) + '">';
                }
                html += '</div>';
                contentEl.innerHTML = html;
                break;

            default:
                contentEl.innerHTML = '';
        }
    }

    // ---------------------------------------------------------------------------
    // Polling — recursive setTimeout so requests never overlap.
    // setInterval fires unconditionally; on a loaded Pi a slow Flask response
    // causes overlapping fetches that can produce back-to-back state transitions
    // (the "catch-up" effect). setTimeout schedules the next poll only after
    // the current fetch resolves, keeping requests serialised.
    // ---------------------------------------------------------------------------
    var lastErrorLogged = false;

    function pollStatus() {
        fetch('/status')
            .then(function (res) {
                if (!res.ok) { throw new Error('HTTP ' + res.status); }
                return res.json();
            })
            .then(function (data) {
                lastErrorLogged = false;

                // Update dev label
                var name = STATE_NAMES[data.state] || String(data.state);
                if (stateValue) { stateValue.textContent = name; }

                // Trigger state entry only on transition
                if (data.state !== currentState) {
                    currentState = data.state;
                    onStateEnter(data.state, data);
                }
            })
            .catch(function (err) {
                if (!lastErrorLogged) {
                    console.warn('Photobooth: lost connection to server', err);
                    lastErrorLogged = true;
                }
            })
            .then(function () {
                // Schedule next poll after this one completes (success or error).
                // .then() after .catch() runs unconditionally when catch returns normally.
                setTimeout(pollStatus, POLL_INTERVAL);
            });
    }

    pollStatus(); // immediate first call; subsequent polls self-schedule
}());
