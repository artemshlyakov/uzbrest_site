'use strict';

const booking = document.querySelector('#booking-dialog');
const gallery = document.querySelector('#gallery-dialog');
const mobileNav = document.querySelector('#mobile-nav');
const navToggle = document.querySelector('.nav-toggle');
const form = document.querySelector('#booking-form');
const dateToggle = document.querySelector('#date-toggle');
const timeToggle = document.querySelector('#time-toggle');
const calendar = document.querySelector('#calendar');
const timePicker = document.querySelector('#time-picker');
const dateInput = document.querySelector('#booking-date');
const timeInput = document.querySelector('#booking-time');
const dateValue = document.querySelector('#date-value');
const timeValue = document.querySelector('#time-value');
const calendarDays = document.querySelector('#calendar-days');
const monthLabel = document.querySelector('#calendar-month');
const previousMonth = document.querySelector('#month-prev');
const nextMonth = document.querySelector('#month-next');
const errorMessage = document.querySelector('#booking-error');
const fallback = document.querySelector('#booking-fallback');

function setNav(open) {
  mobileNav.hidden = !open;
  navToggle.setAttribute('aria-expanded', String(open));
  navToggle.setAttribute('aria-label', open ? 'Закрыть навигацию' : 'Открыть навигацию');
}
navToggle.addEventListener('click', () => setNav(mobileNav.hidden));
mobileNav.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setNav(false)));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !mobileNav.hidden) setNav(false);
});

function syncDialogState() {
  document.body.classList.toggle('modal-open', Boolean(document.querySelector('dialog[open]')));
}
document.querySelectorAll('[data-booking]').forEach(button => button.addEventListener('click', () => {
  setNav(false);
  closePickers();
  clearError();
  booking.showModal();
  syncDialogState();
}));
document.querySelectorAll('dialog').forEach(dialog => {
  dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
  dialog.addEventListener('close', syncDialogState);
});

document.querySelectorAll('[role="tablist"]').forEach(list => {
  const tabs = [...list.querySelectorAll('[role="tab"]')];
  function activate(tab, focus) {
    tabs.forEach(item => {
      const selected = item === tab;
      item.setAttribute('aria-selected', String(selected));
      item.tabIndex = selected ? 0 : -1;
      document.getElementById(item.getAttribute('aria-controls')).hidden = !selected;
    });
    if (focus) tab.focus();
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => activate(tab, false));
    tab.addEventListener('keydown', event => {
      let target;
      if (event.key === 'ArrowRight') target = tabs[(index + 1) % tabs.length];
      if (event.key === 'ArrowLeft') target = tabs[(index - 1 + tabs.length) % tabs.length];
      if (event.key === 'Home') target = tabs[0];
      if (event.key === 'End') target = tabs.at(-1);
      if (target) { event.preventDefault(); activate(target, true); }
    });
  });
});

const photos = [
  ['basilik/dastarkhan.webp', 'За общим столом — иллюстрация Базилика'],
  ['basilik/vladimir.webp', 'Владимир с восточным акцентом'],
  ['basilik/illustrated-menu.webp', 'Наш рисованный дастархан']
];
const drawings = window.TEBURASI_MENU.pages.map(page => [page.src.replace(/^assets\//, ''), page.title]);
let galleryItems = photos;
let galleryIndex = 0;
function renderGallery() {
  const [file, description] = galleryItems[galleryIndex];
  const image = document.querySelector('#gallery-image');
  image.src = window.TEBURASI_ASSETS?.['assets/' + file] || 'assets/' + file;
  image.alt = description;
  document.querySelector('#gallery-description').textContent = description;
  document.querySelector('#gallery-count').textContent = String(galleryIndex + 1) + ' / ' + String(galleryItems.length);
}
function openGallery(index, isArt) {
  galleryItems = isArt ? drawings : photos;
  galleryIndex = index;
  gallery.classList.toggle('art-gallery', isArt);
  gallery.classList.remove('route-gallery');
  gallery.classList.remove('art-zoomed');
  gallery.querySelector('.gallery-zoom').textContent = '+';
  gallery.querySelector('.gallery-zoom').setAttribute('aria-label', 'Увеличить лист');
  renderGallery();
  gallery.showModal();
  syncDialogState();
}
document.querySelectorAll('[data-gallery]').forEach(button => button.addEventListener('click', () => openGallery(Number(button.dataset.gallery), false)));
document.querySelectorAll('[data-art]').forEach(button => button.addEventListener('click', () => openGallery(Number(button.dataset.art), true)));
window.TeburasiGallery = { open: openGallery };

document.querySelector('[data-route-preview]').addEventListener('click', () => {
  openGallery(0, false);
  galleryItems = [['basilik/vladimir.webp', 'Владимир с восточным акцентом — художественная иллюстрация']];
  galleryIndex = 0;
  gallery.classList.add('art-gallery', 'route-gallery');
  gallery.querySelector('.gallery-zoom').setAttribute('aria-label', 'Увеличить схему');
  renderGallery();
});
gallery.querySelector('.gallery-zoom').addEventListener('click', () => {
  const zoomed = gallery.classList.toggle('art-zoomed');
  gallery.querySelector('.gallery-zoom').textContent = zoomed ? '−' : '+';
  const subject = gallery.classList.contains('route-gallery') ? 'схему' : 'лист';
  gallery.querySelector('.gallery-zoom').setAttribute('aria-label', (zoomed ? 'Уменьшить ' : 'Увеличить ') + subject);
});
function moveGallery(direction) {
  galleryIndex = (galleryIndex + direction + galleryItems.length) % galleryItems.length;
  renderGallery();
}
gallery.querySelector('.gallery-prev').addEventListener('click', () => moveGallery(-1));
gallery.querySelector('.gallery-next').addEventListener('click', () => moveGallery(1));
gallery.addEventListener('keydown', event => {
  if (event.key === 'ArrowRight') moveGallery(1);
  if (event.key === 'ArrowLeft') moveGallery(-1);
});

function moscowDateParts() {
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Moscow', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date());
  return Object.fromEntries(parts.filter(part => part.type !== 'literal').map(part => [part.type, Number(part.value)]));
}
function isoDate(date) { return date.toISOString().slice(0, 10); }
function parseDate(value) { return new Date(value + 'T00:00:00Z'); }
const nowMoscow = moscowDateParts();
const today = new Date(Date.UTC(nowMoscow.year, nowMoscow.month - 1, nowMoscow.day));
const lastDate = new Date(today);
lastDate.setUTCDate(lastDate.getUTCDate() + 90);
let visibleMonth = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1));
const dateFormatter = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', timeZone: 'UTC' });
const fullDateFormatter = new Intl.DateTimeFormat('ru-RU', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
const monthFormatter = new Intl.DateTimeFormat('ru-RU', { month: 'long', year: 'numeric', timeZone: 'UTC' });

function closePickers() {
  calendar.hidden = true;
  timePicker.hidden = true;
  dateToggle.setAttribute('aria-expanded', 'false');
  timeToggle.setAttribute('aria-expanded', 'false');
}
function renderCalendar() {
  monthLabel.textContent = monthFormatter.format(visibleMonth);
  calendarDays.replaceChildren();
  const year = visibleMonth.getUTCFullYear();
  const month = visibleMonth.getUTCMonth();
  const offset = (visibleMonth.getUTCDay() + 6) % 7;
  for (let i = 0; i < offset; i++) {
    const spacer = document.createElement('span');
    spacer.setAttribute('aria-hidden', 'true');
    calendarDays.append(spacer);
  }
  const count = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
  for (let day = 1; day <= count; day++) {
    const date = new Date(Date.UTC(year, month, day));
    const value = isoDate(date);
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = String(day);
    button.dataset.date = value;
    button.setAttribute('aria-label', fullDateFormatter.format(date));
    button.setAttribute('aria-pressed', String(value === dateInput.value));
    button.disabled = date < today || date > lastDate;
    if (isoDate(date) === isoDate(today)) button.classList.add('today');
    button.addEventListener('click', () => {
      dateInput.value = value;
      dateValue.textContent = dateFormatter.format(date);
      timeInput.value = '';
      timeValue.textContent = 'Выбрать время';
      clearError();
      closePickers();
      renderCalendar();
      renderTimes();
      timeToggle.focus();
    });
    calendarDays.append(button);
  }
  previousMonth.disabled = year === today.getUTCFullYear() && month === today.getUTCMonth();
  nextMonth.disabled = year === lastDate.getUTCFullYear() && month === lastDate.getUTCMonth();
}
function changeMonth(direction) {
  visibleMonth = new Date(Date.UTC(visibleMonth.getUTCFullYear(), visibleMonth.getUTCMonth() + direction, 1));
  renderCalendar();
}
previousMonth.addEventListener('click', () => changeMonth(-1));
nextMonth.addEventListener('click', () => changeMonth(1));
dateToggle.addEventListener('click', () => {
  const open = calendar.hidden;
  closePickers();
  if (!open) return;
  renderCalendar();
  calendar.hidden = false;
  dateToggle.setAttribute('aria-expanded', 'true');
  (calendarDays.querySelector('[aria-pressed="true"]') || calendarDays.querySelector('button:not(:disabled)'))?.focus();
});
calendarDays.addEventListener('keydown', event => {
  const button = event.target.closest('button');
  if (!button) return;
  const enabled = [...calendarDays.querySelectorAll('button:not(:disabled)')];
  const index = enabled.indexOf(button);
  let newIndex;
  if (event.key === 'ArrowRight') newIndex = index + 1;
  if (event.key === 'ArrowLeft') newIndex = index - 1;
  if (event.key === 'ArrowDown') newIndex = index + 7;
  if (event.key === 'ArrowUp') newIndex = index - 7;
  if (event.key === 'Home') newIndex = 0;
  if (event.key === 'End') newIndex = enabled.length - 1;
  if (newIndex !== undefined) {
    event.preventDefault();
    enabled[Math.max(0, Math.min(enabled.length - 1, newIndex))]?.focus();
  }
});
// Booking slots will be supplied by the restaurant after opening hours are confirmed.
function desiredTimes() { return []; }
let timeDayOffset = 0;
function renderTimes() {
  const target = document.querySelector('#time-options');
  target.replaceChildren();
  if (!dateInput.value) {
    const note = document.createElement('p');
    note.className = 'empty-times';
    note.textContent = 'Сначала выбери день нашей встречи.';
    target.append(note);
    return;
  }
  const slots = desiredTimes(parseDate(dateInput.value));
  if (!slots.length) {
    const note = document.createElement('p');
    note.className = 'empty-times';
    note.textContent = 'На сегодня уже поздно. Давай выберем другой день?';
    target.append(note);
  }
  slots.forEach(slot => {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = slot.value + (slot.dayOffset ? ' ⁺¹' : '');
    button.setAttribute('aria-label', slot.value + (slot.dayOffset ? ', после полуночи' : ''));
    button.setAttribute('aria-pressed', String(timeInput.value === slot.value));
    button.addEventListener('click', () => {
      timeInput.value = slot.value;
      timeDayOffset = slot.dayOffset;
      timeValue.textContent = slot.value + (slot.dayOffset ? ' ⁺¹' : '');
      clearError();
      closePickers();
      timeToggle.focus();
    });
    target.append(button);
  });
  if (slots.some(slot => slot.dayOffset)) {
    const note = document.createElement('p');
    note.className = 'after-midnight';
    note.textContent = '⁺¹ Уже после полуночи';
    target.append(note);
  }
}
timeToggle.addEventListener('click', () => {
  const open = timePicker.hidden;
  closePickers();
  if (!open) return;
  renderTimes();
  timePicker.hidden = false;
  timeToggle.setAttribute('aria-expanded', 'true');
  timePicker.querySelector('button')?.focus();
});
booking.addEventListener('click', event => {
  if (!event.target.closest('.booking-date,.booking-time')) closePickers();
});
booking.addEventListener('cancel', event => {
  if (!calendar.hidden || !timePicker.hidden) {
    event.preventDefault();
    const wasCalendar = !calendar.hidden;
    closePickers();
    (wasCalendar ? dateToggle : timeToggle).focus();
  }
});
function guestLabel(value) {
  if (value === 1) return '1 гость';
  if (value >= 2 && value <= 4) return String(value) + ' гостя';
  return String(value) + ' гостей';
}
const guestInput = document.querySelector('#booking-guests');
const guestMinus = document.querySelector('#guest-minus');
const guestPlus = document.querySelector('#guest-plus');
function updateGuests(change) {
  const count = Math.max(1, Math.min(12, Number(guestInput.value) + change));
  guestInput.value = String(count);
  document.querySelector('#guest-value').value = guestLabel(count);
  guestMinus.disabled = count === 1;
  guestPlus.disabled = count === 12;
}
guestMinus.addEventListener('click', () => updateGuests(-1));
guestPlus.addEventListener('click', () => updateGuests(1));
updateGuests(0);

function clearError() {
  errorMessage.hidden = true;
  fallback.hidden = true;
  form.querySelectorAll('[aria-invalid]').forEach(field => {
    field.removeAttribute('aria-invalid');
    field.removeAttribute('aria-describedby');
  });
}
function showError(message, field) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
  if (field) {
    field.setAttribute('aria-invalid', 'true');
    field.setAttribute('aria-describedby', 'booking-error');
    field.focus();
  }
}
form.addEventListener('input', clearError);
document.querySelector('#booking-phone').addEventListener('blur', event => {
  const digits = event.target.value.replace(/\D/g, '');
  if (digits.length === 11 && /^[78]/.test(digits)) {
    event.target.value = '+7 (' + digits.slice(1, 4) + ') ' + digits.slice(4, 7) + '-' + digits.slice(7, 9) + '-' + digits.slice(9);
  }
});

// Replace this adapter with a same-origin server integration after the venue
// supplies its provider ID and approves data processing. Never put API keys here.
// It must return status "received" only after the provider accepts the request.
const bookingGateway = {
  async submit(request) {
    void request;
    return { status: 'unavailable' };
  }
};
form.addEventListener('submit', async event => {
  event.preventDefault();
  closePickers();
  clearError();
  if (!dateInput.value) { showError('Выбери день нашей встречи.', dateToggle); return; }
  const selectedDate = parseDate(dateInput.value);
  if (selectedDate < today || selectedDate > lastDate) { showError('Пожалуйста, выбери другую дату.', dateToggle); return; }
  const desired = desiredTimes(selectedDate).find(slot => slot.value === timeInput.value && slot.dayOffset === timeDayOffset);
  if (!desired) { showError('Выбери подходящее время.', timeToggle); return; }
  const nameField = document.querySelector('#booking-name');
  const phoneField = document.querySelector('#booking-phone');
  const name = nameField.value.trim();
  const phone = phoneField.value.trim();
  const phoneDigits = phone.replace(/\D/g, '');
  if (name.length < 2) { showError('Подскажи, как тебя зовут.', nameField); return; }
  if (phoneDigits.length < 10 || phoneDigits.length > 15 || !/^[+\d\s()—-]+$/.test(phone)) {
    showError('Проверь номер телефона — нам нужно ответить тебе.', phoneField); return;
  }
  const serviceDate = new Date(selectedDate);
  serviceDate.setUTCDate(serviceDate.getUTCDate() + desired.dayOffset);
  const request = {
    venue: 'basilik',
    serviceDate: dateInput.value,
    startsAt: isoDate(serviceDate) + 'T' + timeInput.value + ':00+03:00',
    timezone: 'Europe/Moscow',
    guests: Number(guestInput.value),
    guest: { name, phone: '+' + (phoneDigits.length === 11 && phoneDigits.startsWith('8') ? '7' + phoneDigits.slice(1) : phoneDigits) },
    comment: document.querySelector('#booking-comment').value.trim()
  };
  const submit = document.querySelector('#booking-submit');
  submit.disabled = true;
  submit.setAttribute('aria-busy', 'true');
  try {
    const response = await bookingGateway.submit(request);
    if (response.status === 'received') {
      errorMessage.textContent = 'Спасибо! Команда бара свяжется с тобой и подтвердит бронь.';
      errorMessage.hidden = false;
      form.reset();
      dateValue.textContent = 'Выбрать дату';
      timeValue.textContent = 'Выбрать время';
      updateGuests(0);
    } else {
      showError('Онлайн-бронирование пока не открыто. Скоро здесь можно будет оставить заявку.');
      fallback.hidden = false;
    }
  } catch {
    showError('Онлайн-бронирование пока не открыто. Скоро здесь можно будет оставить заявку.');
    fallback.hidden = false;
  } finally {
    submit.disabled = false;
    submit.removeAttribute('aria-busy');
  }
});

if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  document.body.classList.add('has-motion');
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach(element => observer.observe(element));
}
