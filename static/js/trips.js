const tripPanel = document.querySelector('#trip-panel');
const tripListArea = document.querySelector('#trip-list-area');
const createForm = document.querySelector('#trip-create-form');
const dashboardMessage = document.querySelector('#dashboard-message');
const csrfToken = createForm?.querySelector('input[name="csrf_token"]').value;
const tripCount = document.querySelector('#trip-count');
const tripStatuses = ['Planned', 'Ongoing', 'Completed'];
const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function tripSchedule(startDate, endDate) {
  const [startYear, startMonth, startDay] = startDate.split('-').map(Number);
  const [endYear, endMonth, endDay] = endDate.split('-').map(Number);
  const nights = Math.round((Date.UTC(endYear, endMonth - 1, endDay) - Date.UTC(startYear, startMonth - 1, startDay)) / 86400000);
  return {
    startMonth: monthNames[startMonth - 1],
    startDay,
    dateRange: `${monthNames[startMonth - 1]} ${startDay} – ${monthNames[endMonth - 1]} ${endDay}, ${endYear}`,
    nights: nights === 0 ? 'Day trip' : `${nights} night${nights === 1 ? '' : 's'}`,
  };
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'})[character]);
}

function showMessage(text) {
  dashboardMessage.textContent = text;
  dashboardMessage.hidden = false;
  dashboardMessage.scrollIntoView({block: 'nearest'});
}

async function callApi(method, path, body) {
  const response = await fetch(path, {
    method,
    headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken},
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error?.message || 'Something went wrong. Please try again.');
  return data;
}

function tripPayload(form) {
  const values = Object.fromEntries(new FormData(form));
  return {
    title: values.title,
    destination_id: values.destination_id,
    start_date: values.start_date,
    end_date: values.end_date,
    budget: Number(values.budget),
    status: values.status,
    description: values.description,
  };
}

function tripCard(trip) {
  const id = escapeHtml(trip._id);
  const csrf = `<input type="hidden" name="csrf_token" value="${escapeHtml(csrfToken)}">`;
  const statusOptions = tripStatuses.map(status => `<option${status === trip.status ? ' selected' : ''}>${status}</option>`).join('');
  const schedule = tripSchedule(trip.start_date, trip.end_date);
  return `<article class="trip-card" data-trip-id="${id}">
    <div class="trip-date" aria-hidden="true"><span>${schedule.startMonth}</span><strong>${schedule.startDay}</strong></div>
    <div class="trip-body">
      <div class="trip-top"><p class="trip-destination">${escapeHtml(trip.destination.name)}</p><span class="status status-${escapeHtml(trip.status.toLowerCase())}">${escapeHtml(trip.status)}</span></div>
      <h3>${escapeHtml(trip.title)}</h3>
      <ul class="trip-meta"><li>${schedule.dateRange}</li><li>${schedule.nights}</li><li>$${escapeHtml(trip.budget)} budget</li></ul>
      ${trip.description ? `<p class="trip-notes">${escapeHtml(trip.description)}</p>` : ''}
      <div class="trip-actions-row">
        <details class="trip-edit"><summary class="text-button">Edit trip</summary>
          <form class="dashboard-form trip-edit-form" method="post" action="/dashboard/trips/${id}/edit">${csrf}
            <input type="hidden" name="destination_id" value="${escapeHtml(trip.destination_id)}">
            <label><span>Trip title</span><input name="title" maxlength="200" value="${escapeHtml(trip.title)}" required></label>
            <label><span>Destination</span><input value="${escapeHtml(trip.destination.name)}" disabled></label>
            <label><span>Start date</span><input name="start_date" type="date" value="${escapeHtml(trip.start_date)}" required></label>
            <label><span>End date</span><input name="end_date" type="date" value="${escapeHtml(trip.end_date)}" required></label>
            <label><span>Budget</span><input name="budget" type="number" min="0" step="0.01" value="${escapeHtml(trip.budget)}" required></label>
            <label><span>Status</span><select name="status">${statusOptions}</select></label>
            <label class="dashboard-form-full"><span>Notes</span><textarea name="description" rows="3">${escapeHtml(trip.description)}</textarea></label>
            <div class="dashboard-form-full"><button class="primary" type="submit">Save changes</button></div>
          </form>
        </details>
        <form class="trip-delete-form" method="post" action="/dashboard/trips/${id}/delete">${csrf}<button class="text-button text-danger" type="submit">Delete</button></form>
      </div>
    </div>
  </article>`;
}

async function refreshTrips() {
  const {trips} = await callApi('GET', '/api/trips');
  tripCount.textContent = trips.length;
  tripListArea.innerHTML = trips.length
    ? `<div class="trip-list">${trips.map(tripCard).join('')}</div>`
    : '<p class="empty-state">No trips yet. Plan your first one with the form.</p>';
}

async function runTripAction(action, successText) {
  try {
    await action();
    await refreshTrips();
    showMessage(successText);
  } catch (error) {
    showMessage(error.message);
  }
}

createForm?.addEventListener('submit', event => {
  event.preventDefault();
  runTripAction(async () => {
    await callApi('POST', '/api/trips', tripPayload(createForm));
    createForm.reset();
  }, 'Trip added.');
});

tripPanel?.addEventListener('submit', event => {
  const form = event.target;
  const tripId = form.closest('[data-trip-id]')?.dataset.tripId;
  if (!tripId) return;
  event.preventDefault();
  if (form.matches('.trip-edit-form')) {
    runTripAction(() => callApi('PUT', `/api/trips/${tripId}`, tripPayload(form)), 'Trip updated.');
  } else if (form.matches('.trip-delete-form')) {
    runTripAction(() => callApi('DELETE', `/api/trips/${tripId}`), 'Trip deleted.');
  }
});
