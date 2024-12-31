// Global error handler
window.onerror = function(msg, url, lineNo, columnNo, error) {
    console.error('Error: ' + msg + '\nURL: ' + url + '\nLine: ' + lineNo + '\nColumn: ' + columnNo + '\nError object: ' + JSON.stringify(error));
    showNotification('An error occurred. Please refresh the page if issues persist.');
    return false;
};

// Configuration constants
const CONSTANTS = {
    RETRY_TIMEOUT: 15000,
    MAX_RETRY_TIMEOUT: 60000,
    INITIAL_DELAY: 5000,
    NOTIFICATION_DURATION: 5000,
    MANUAL_PING_ERROR_DURATION: 2000,
    RATE_LIMIT_WAIT: 5000,
    UPDATE_DELAY: 1500
};

// System variables for managing scheduled ping timing and countdown display
let nextScheduledPingTime = null;  // Stores the next ping timestamp
let lastScheduledCheck = false;
let isCheckingPing = false;  // Add a lock to prevent concurrent checks
let retryTimeout = CONSTANTS.RETRY_TIMEOUT;    // Default retry timeout

// Protected URLs will be fetched from server
let TARGET_URLS = [];

// Fetch TARGET_URLS from server on initialization
async function initializeTargetUrls() {
    try {
        const response = await fetch('/api/target-urls');
        await handleAuthError(response);
        if (!response.ok) {
            throw new Error('Failed to fetch target URLs');
        }
        TARGET_URLS = await response.json();
        console.log('Target URLs initialized successfully');
    } catch (error) {
        console.error('Error initializing target URLs:', error);
        showNotification('Error initializing application. Please refresh.');
    }
}

// Helper function for creating table rows
function createTableRow(ping, index) {
    const statusClass = ping.status === 'Success' ? 'success' : 'failure';
    const responseClass = ping.response_time > 1000 ? 'slow-response' : '';

    return `<tr>
        <td>${index}</td>
        <td>${ping.url}</td>
        <td>${ping.timestamp}</td>
        <td class="${responseClass}">${ping.response_time}ms</td>
        <td>${ping.status_code}</td>
        <td class="${statusClass}">${ping.status}</td>
        <td>${ping.uptime}%</td>
    </tr>`;
}

// Show notification function
function showNotification(message, duration = 5000) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, duration);
}

// Check if scheduled ping is imminent
async function isScheduledPingImminent() {
    try {
        const response = await fetch('/check-scheduled-ping', {
        });
        await handleAuthError(response);
        const data = await response.json();
        return {
            imminent: data.imminent,
            remainingTime: Math.ceil(data.remainingTime) // Round up to nearest second
        };
    } catch (error) {
        console.error('Error checking scheduled ping:', error);
        return { imminent: false, remainingTime: 0 };
    }
}

// Manual ping function
async function manualPing(urlIndex) {
    const buttons = document.querySelectorAll('.ping-button');
    const button = buttons[urlIndex];
    
    // Disable button and show loading state
    button.disabled = true;
    const originalText = button.textContent;
    button.textContent = 'Pinging...';

    try {
        const response = await fetch(`/ping/${urlIndex}`, {
        });
        await handleAuthError(response);
        const data = await response.json();
        
        if (response.status === 423) {
            // Scheduled ping is imminent
            const remainingTime = Math.ceil(data.remainingTime);  // Round up to nearest second
            showNotification(`Manual ping rejected - scheduled ping in ${remainingTime} seconds`);

            buttons.forEach(btn => {
                if (!btn.getAttribute('data-original-text')) {
                    btn.setAttribute('data-original-text', btn.textContent);
                }
                btn.disabled = true;
                btn.style.backgroundColor = '#666666'; // Grey out the button
            });

            let countdown = remainingTime;
            const localInterval = setInterval(() => {
                countdown--;
                if (countdown <= 0) {
                    clearInterval(localInterval);
                    buttons.forEach(btn => {
                        btn.disabled = false;
                        btn.style.backgroundColor = '';
                        btn.textContent = btn.getAttribute('data-original-text');
                    });
                    updatePageData();
                    return;
                }

                buttons.forEach(btn => {
                    const originalText = btn.getAttribute('data-original-text');
                    btn.textContent = `${originalText} (${countdown}s)`;
                });
            }, 1000);
            return;
        }

        if (response.status === 429) {
            // Rate limit hit
            showNotification("Too many requests. Please wait.");
            button.style.backgroundColor = '#faa61a';
            button.textContent = 'Too Many Requests';
            setTimeout(() => {
                button.style.backgroundColor = '';
                button.textContent = originalText;
                button.disabled = false;
            }, 5000);
            return;
        }
        
        button.style.backgroundColor = data.status === 'success' ? '#4CAF50' : '#f44336';
        button.textContent = data.status === 'success' ? 'Success!' : 'Failed!';
        
        setTimeout(() => {
            updatePageData();
        }, 1500);
        
    } catch (error) {
        console.error('Error during manual ping:', error);
        button.style.backgroundColor = '#f44336';
        button.textContent = 'Error!';
        showNotification("Error occurred during ping");
        
        setTimeout(() => {
            button.style.backgroundColor = '';
            button.textContent = originalText;
            button.disabled = false;
            updatePageData();
        }, 2000);
    }
}

// Clock update function
function updateClock() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const date = now.toLocaleDateString('en-IN', options);
    const time = now.toLocaleTimeString('en-IN', { hour12: false });
    document.getElementById('date').textContent = date;
    document.getElementById('time').textContent = time;
}

async function checkScheduledPing() {
    if (isCheckingPing) return;  // If already checking, skip
    try {
        isCheckingPing = true;  // Set lock
        const { imminent, remainingTime } = await isScheduledPingImminent();
        lastScheduledCheck = imminent;
        retryTimeout = CONSTANTS.RETRY_TIMEOUT;  // Reset retry timeout on success
        
        // Synchronize local timer with server's schedule
        nextScheduledPingTime = Date.now() + (remainingTime * 1000);

        // Update display and validate client-side timer accuracy
        updateNextPingDisplay(remainingTime);
        
        if (remainingTime <= 0) {
            updatePageData();
        }
    } catch (error) {
        console.error('Error checking scheduled ping:', error);
        document.getElementById('next-ping-button').textContent = 'Next Ping: --:--';
        if (error.status === 429) {
            // If rate limited, increase retry timeout
            retryTimeout = Math.min(retryTimeout * 2, 60000); // Max 1 minute
            console.log(`Rate limited. Retrying in ${retryTimeout/1000} seconds`);
        }
    } finally {
        isCheckingPing = false;  // Release lock
    }
}

// Timer System: Manages countdown display and updates for scheduled pings
function startCountdownTimer() {
    const timerInterval = window.setInterval(() => {
        if (nextScheduledPingTime) {
            const now = Date.now();
            const remainingTime = Math.max(0, Math.ceil((nextScheduledPingTime - now) / 1000));
            updateNextPingDisplay(remainingTime);
        }
    }, 1000);
    // Store interval ID for cleanup if needed
    window.countdownTimerInterval = timerInterval;
}

function updateNextPingDisplay(remainingTime) {
    const button = document.getElementById('next-ping-button');
    if (button) {
        const minutes = Math.floor(remainingTime / 60);
        const seconds = remainingTime % 60;
        button.textContent = `Next Ping: ${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}

// Initialize ping checker with rate limit protection and exponential backoff
function startPingChecks() {
    // Initialize live countdown timer
    startCountdownTimer();
    // Initial check with delay
    setTimeout(async () => {
        await checkScheduledPing();
        // Start recurring checks
        const checkInterval = window.setInterval(async () => {
            await checkScheduledPing();
        }, retryTimeout);
        // Store interval ID for cleanup if needed
        window.pingCheckInterval = checkInterval;
    }, 5000);  // Initial 5-second delay
}

// Start the ping checks
startPingChecks();

// Start the clock
setInterval(updateClock, 1000);
updateClock();

// Check if we have credentials
function checkAuth() {
    // Make a test request to check auth status
    return fetch('/api/ping-history')
    .then(response => {
        if (response.ok) {
            document.getElementById('authOverlay').style.display = 'none';
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('logoutBtn').style.display = 'block';
            return true;
        } else {
            document.getElementById('authOverlay').style.display = 'block';
            document.getElementById('loginForm').style.display = 'block';
            document.getElementById('logoutBtn').style.display = 'none';
            return false;
        }
    })
    .catch(() => {
        document.getElementById('authOverlay').style.display = 'block';
        document.getElementById('loginForm').style.display = 'block';
        document.getElementById('logoutBtn').style.display = 'none';
        return false;
    });   
}

// Login function
function login() {
    const loginButton = document.getElementById('loginButton');
    const errorDiv = document.getElementById('loginError');
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!username || !password) {
        errorDiv.textContent = 'Please enter both username and passphrase';
        errorDiv.style.display = 'block';
        return;
    }

    loginButton.disabled = true;
    loginButton.textContent = 'Logging in...';
    errorDiv.style.display = 'none';

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    }).then(response => {
        if (response.ok) {
            document.getElementById('authOverlay').style.display = 'none';
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('logoutBtn').style.display = 'block';
            updatePageData();
        } else {
            throw new Error('Invalid credentials');
        }
    }).catch(error => {
        errorDiv.textContent = error.message || 'Login failed';
        errorDiv.style.display = 'block';
    }).finally(() => {
        loginButton.disabled = false;
        loginButton.textContent = 'Login';
    });
}

// Logout function
function logout() {
    fetch('/logout', {
        method: 'POST'
    }).then(response => {
        if (response.ok) {
            document.getElementById('authOverlay').style.display = 'block';
            document.getElementById('loginForm').style.display = 'block';
            document.getElementById('logoutBtn').style.display = 'none';
        }
    }).catch(error => {
        console.error('Logout failed:', error);
    });
}

// Handle enter key in login form
document.getElementById('password').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        login();
    }
});

// Initialize app on page load
document.addEventListener('DOMContentLoaded', async () => {
    await initializeTargetUrls();
    checkAuth();
});

// Add error handler for 401 responses
function handleAuthError(response) {
    if (response.status === 401) {
        checkAuth();
        throw new Error('Session expired. Please login again.');
    }
    return response;
}

// Add the updatePageData function
async function updatePageData() {
    try {
        const historyResponse = await fetch('/api/ping-history');
        if (!historyResponse.ok && historyResponse.status !== 401) {
            throw new Error(`HTTP error! status: ${historyResponse.status}`);
        }
        await handleAuthError(historyResponse);
        const historyData = await historyResponse.json();

        // Update tables
        for (let i = 1; i <= 3; i++) {
            const table = document.getElementById(`table${i}`);
            if (!table) continue;
            const tbody = table.querySelector('tbody');
            if (tbody && historyData[TARGET_URLS[i-1]]) {
                tbody.innerHTML = historyData[TARGET_URLS[i-1]]
                .map((ping, index) => createTableRow(ping, index + 1))
                .join('');
            }
        }
        // Re-enable buttons
        document.querySelectorAll('.ping-button').forEach(button => {
            button.disabled = false;
            button.style.backgroundColor = '';
            if (button.getAttribute('data-original-text')) {
                button.textContent = button.getAttribute('data-original-text');
            }
        });
    } catch (error) {
        console.error('Error updating page data:', error);
        showNotification('Error updating page data');
    }
}
