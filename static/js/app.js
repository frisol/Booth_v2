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
    var llamaFrame  = document.getElementById('llama-frame');

    // ---------------------------------------------------------------------------
    // Llama animation
    // ---------------------------------------------------------------------------
    var llamaFrameIdx = 0;
    var llamaTimer    = null;

    function startLlama() {
        if (llamaTimer) return;
        llamaTimer = setInterval(function () {
            llamaFrameIdx = 1 - llamaFrameIdx;
            llamaFrame.src = '/static/dev/llama_dance_' + llamaFrameIdx + '.png';
        }, 250); // 4 fps — classic 8-bit feel
    }

    function stopLlama() {
        if (llamaTimer) { clearInterval(llamaTimer); llamaTimer = null; }
        llamaFrameIdx = 0;
        llamaFrame.src = '/static/dev/llama_dance_0.png';
    }

    // ---------------------------------------------------------------------------
    // Review photo cycling (state 8)
    // ---------------------------------------------------------------------------
    var reviewTimer  = null;
    var reviewPhotos = [];
    var reviewDuration = 2000; // ms — updated from server on state 8 entry

    function clearReview() {
        if (reviewTimer) { clearTimeout(reviewTimer); reviewTimer = null; }
        reviewPhotos = [];
    }

    function startReview(photos, durationSecs) {
        clearReview();
        reviewPhotos  = photos.slice();
        reviewDuration = durationSecs * 1000;
        var idx = 0;

        function showNext() {
            if (idx >= reviewPhotos.length) return;
            contentEl.innerHTML =
                '<img class="review-photo" src="' + reviewPhotos[idx] + '" alt="Photo ' + (idx + 1) + '">';
            idx++;
            if (idx < reviewPhotos.length) {
                reviewTimer = setTimeout(showNext, reviewDuration);
            }
        }
        showNext();
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
        // Clear any running review cycle
        clearReview();

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
                startReview(
                    data.photos || [],
                    data.review_photo_duration || 2
                );
                break;

            default:
                contentEl.innerHTML = '';
        }
    }

    // ---------------------------------------------------------------------------
    // Polling
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
            });
    }

    setInterval(pollStatus, POLL_INTERVAL);
    pollStatus(); // immediate call on load
}());
