/* Adapt cloud responses to the shared Neural Terminal's read-only data contract. */
'use strict';
window.NeuralCloud = {
    async load(get, signal, choice) {
        const [state, registry, sessions] = await Promise.all([
            get('/api/dashboard/state', signal), get('/api/employees', signal),
            get('/api/sessions', signal)
        ]);
        const latest = !['auto', 'latest'].includes(choice)
            ? sessions.find(s => s.session_id === choice) || null : sessions[0] || null;
        let rows = null, snapshot = [], rosterActive = null;
        if (latest) {
            const detail = await get('/api/sessions/' + encodeURIComponent(latest.session_id), signal);
            snapshot = detail.snapshot || [];
            if (['review', 'ready', 'exported'].includes(latest.status)) rows = detail.results || [];
            if (detail.employee_registry?.employees)
                rosterActive = detail.employee_registry.employees.filter(p => p.active).length;
        }
        return {...state, employees: registry.employees || [], sessions, latest,
                rows, snapshot, rosterActive, skippedSession: null};
    }
};
window.openSession = async sessionId => {
    sid = sessionId;
    await loadSession();
};
