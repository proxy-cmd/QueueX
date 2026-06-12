(function () {
    function text(selector, value) {
        var element = document.querySelector(selector);
        if (element) {
            element.textContent = value;
        }
    }

    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, function (char) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;',
            }[char];
        });
    }

    function statusClass(status) {
        return 'status status-' + status;
    }

    function showMessage(message) {
        var stack = document.querySelector('.message-stack');
        if (!stack || !message) {
            return;
        }

        stack.innerHTML = '<p class="message">' + escapeHtml(message) + '</p>';
    }

    function actionButtons(token) {
        var complete = '';
        var cancel = '';

        if (token.status !== 'completed') {
            complete = [
                '<form method="post" action="/tokens/',
                token.id,
                '/complete/" data-live-action>',
                csrfInput(),
                '<button type="submit">Complete</button>',
                '</form>',
            ].join('');
        }

        if (token.status === 'waiting' || token.status === 'serving') {
            cancel = [
                '<form method="post" action="/tokens/',
                token.id,
                '/cancel/" data-live-action>',
                csrfInput(),
                '<button type="submit">Cancel</button>',
                '</form>',
            ].join('');
        }

        return complete + cancel;
    }

    function csrfInput() {
        var token = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (!token) {
            return '';
        }

        return '<input type="hidden" name="csrfmiddlewaretoken" value="' + escapeHtml(token.value) + '">';
    }

    function updateReception(payload) {
        text('[data-live="total-waiting"]', payload.stats.total_waiting);
        text('[data-live="completed-today"]', payload.stats.completed_today);
        text('[data-live="current-serving"]', payload.stats.current_serving || 'None');

        var table = document.querySelector('[data-live="queue-table"]');
        if (!table) {
            return;
        }

        if (!payload.tokens.length) {
            table.innerHTML = '<tr><td colspan="5" class="empty-row">No patients in queue yet.</td></tr>';
            return;
        }

        table.innerHTML = payload.tokens.map(function (token) {
            return [
                '<tr>',
                '<td><strong>', escapeHtml(token.token_number), '</strong></td>',
                '<td>', escapeHtml(token.patient_name), '</td>',
                '<td>', escapeHtml(token.patient_phone), '</td>',
                '<td><span class="', statusClass(token.status), '">',
                escapeHtml(token.status_label),
                '</span></td>',
                '<td class="action-cell">', actionButtons(token), '</td>',
                '</tr>',
            ].join('');
        }).join('');
    }

    function updatePatient(payload) {
        var shell = document.querySelector('[data-patient-token]');
        if (!shell) {
            return;
        }

        var ownToken = shell.getAttribute('data-patient-token');
        var token = payload.tokens.find(function (item) {
            return item.token_number === ownToken;
        });

        text('[data-live="patient-now-serving"]', payload.current_serving ? payload.current_serving.token_number : 'Not started');

        if (!token) {
            text('[data-live="patient-status"]', 'Cancelled');
            text('[data-live="patient-people-ahead"]', '0');
            text('[data-live="patient-estimated-wait"]', '0 min');
            return;
        }

        text('[data-live="patient-status"]', token.status_label);
        text('[data-live="patient-people-ahead"]', token.people_ahead);
        text('[data-live="patient-estimated-wait"]', token.estimated_wait + ' min');
    }

    function updateDisplay(payload) {
        text('[data-live="display-queue-length"]', payload.queue_length);
        text('[data-live="display-serving"]', payload.current_serving ? payload.current_serving.token_number : '--');
        text('[data-live="display-estimated-wait"]', payload.estimated_wait + ' min');

        var upcoming = document.querySelector('[data-live="display-upcoming"]');
        if (!upcoming) {
            return;
        }

        if (!payload.upcoming_tokens.length) {
            upcoming.innerHTML = '<span>No waiting tokens</span>';
            return;
        }

        upcoming.innerHTML = payload.upcoming_tokens.map(function (token) {
            return '<span>' + escapeHtml(token.token_number) + '</span>';
        }).join('');
    }

    function applyPayload(payload) {
        updateReception(payload);
        updatePatient(payload);
        updateDisplay(payload);
    }

    function connectQueueSocket() {
        if (!window.WebSocket) {
            return;
        }

        var protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        var socket = new WebSocket(protocol + window.location.host + '/ws/queue/');

        socket.onmessage = function (event) {
            var data = JSON.parse(event.data);
            if (data.payload) {
                applyPayload(data.payload);
            }
        };

        socket.onclose = function () {
            window.setTimeout(connectQueueSocket, 2000);
        };
    }

    document.addEventListener('submit', function (event) {
        var form = event.target;
        if (!form.matches('[data-live-action]')) {
            return;
        }

        event.preventDefault();

        fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('Request failed');
                }
                return response.json();
            })
            .then(function (data) {
                showMessage(data.message);
                if (form.classList.contains('stack-form')) {
                    form.reset();
                }
            })
            .catch(function () {
                form.submit();
            });
    });

    connectQueueSocket();
}());
