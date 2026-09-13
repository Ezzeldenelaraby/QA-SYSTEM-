/* QMS Hub JavaScript Utilities */

document.addEventListener('DOMContentLoaded', function() {
    // 1. Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarWrapper = document.getElementById('sidebar-wrapper');
    if (sidebarToggle && sidebarWrapper) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            sidebarWrapper.classList.toggle('toggled');
        });
    }

    // 2. Auto Dismiss Flash Alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 6000);
    });

    // 3. Dynamic Risk Score & Level live computation
    const likelihoodSelect = document.getElementById('id_likelihood');
    const severitySelect = document.getElementById('id_severity');
    const riskScoreDisplay = document.getElementById('riskScoreDisplay');
    const riskLevelDisplay = document.getElementById('riskLevelDisplay');

    function updateRiskCalculation() {
        if (likelihoodSelect && severitySelect && riskScoreDisplay) {
            const l = parseInt(likelihoodSelect.value) || 1;
            const s = parseInt(severitySelect.value) || 1;
            const score = l * s;
            riskScoreDisplay.textContent = score;

            let level = "Low";
            let badgeClass = "badge-green";
            if (score >= 15) {
                level = "Critical";
                badgeClass = "badge-red";
            } else if (score >= 10) {
                level = "High";
                badgeClass = "badge-red";
            } else if (score >= 5) {
                level = "Medium";
                badgeClass = "badge-yellow";
            }

            if (riskLevelDisplay) {
                riskLevelDisplay.textContent = level;
                riskLevelDisplay.className = "badge " + badgeClass;
            }
        }
    }

    if (likelihoodSelect && severitySelect) {
        likelihoodSelect.addEventListener('change', updateRiskCalculation);
        severitySelect.addEventListener('change', updateRiskCalculation);
        updateRiskCalculation();
    }
});

// 4. Mark Notification Read via Fetch API
function markNotificationRead(notifId, element) {
    fetch(`/notifications/mark-read/${notifId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (element) {
                element.classList.remove('fw-bold');
                element.classList.add('text-muted');
            }
            const countBadge = document.getElementById('unreadNotifBadge');
            if (countBadge) {
                let current = parseInt(countBadge.textContent) || 0;
                if (current > 1) {
                    countBadge.textContent = current - 1;
                } else {
                    countBadge.remove();
                }
            }
        }
    })
    .catch(err => console.error('Error marking notification:', err));
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
