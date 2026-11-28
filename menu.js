'use strict';
(() => {
  const data = window.TEBURASI_MENU;
  const landing = document.querySelector('#landing-site');
  const page = document.querySelector('#full-menu-page');
  const results = document.querySelector('#catalog-results');
  const search = document.querySelector('#menu-search');
  const clear = document.querySelector('#clear-menu-search');
  const categories = document.querySelector('#catalog-categories');
  const dishDialog = document.querySelector('#dish-dialog');
  const initialTitle = document.title;
  let kind = 'food';
  let category = 'all';
  let mode = 'photos';
  let landingScroll = 0;
  let rendered = false;
  const foodFilters = [['all', 'Вся кухня'], ['Горячие блюда', 'Горячее'], ['Супы', 'Супы'], ['Мангал', 'Мангал'], ['Выпечка', 'Выпечка'], ['Салаты', 'Салаты'], ['Десерты', 'Сладкое']];
  const barFilters = [['all', 'Все напитки']];
  const formatter = new Intl.NumberFormat('ru-RU');
  function asset(src) { return window.TEBURASI_ASSETS?.[src] || src; }
  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function money(value) { return value == null ? '' : formatter.format(value) + ' ₽'; }
  function positionCount(value) {
    const last = value % 10;
    const hundred = value % 100;
    const ending = hundred >= 11 && hundred <= 14 ? 'позиций' : last === 1 ? 'позиция' : last >= 2 && last <= 4 ? 'позиции' : 'позиций';
    return String(value) + ' ' + ending;
  }
  function normalize(text) { return String(text || '').toLocaleLowerCase('ru').replaceAll('ё', 'е').normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
  function barGroup() { return 'all'; }
  function photoNode(item, className = '') {
    const frame = element('div', 'catalog-photo ' + className);
    const photo = item.photo;
    if (!photo) return frame;
    if (photo.crop) {
      const ns = 'http://www.w3.org/2000/svg';
      const svg = document.createElementNS(ns, 'svg');
      svg.setAttribute('viewBox', photo.crop.join(' '));
      svg.setAttribute('preserveAspectRatio', 'xMidYMid slice');
      svg.setAttribute('role', 'img');
      svg.setAttribute('aria-label', item.name);
      const image = document.createElementNS(ns, 'image');
      image.setAttribute('href', asset(photo.src));
      image.setAttribute('width', String(photo.width));
      image.setAttribute('height', String(photo.height));
      svg.append(image);
      frame.append(svg);
    } else {
      const image = document.createElement('img');
      image.src = asset(photo.src);
      image.alt = item.name;
      image.loading = 'lazy';
      image.decoding = 'async';
      frame.append(image);
    }
    return frame;
  }
  function showDish(item) {
    document.querySelector('#dish-photo').replaceChildren(photoNode(item));
    document.querySelector('#dish-category').textContent = item.category;
    document.querySelector('#dish-name').textContent = item.name;
    document.querySelector('#dish-description').textContent = item.description;
    document.querySelector('#dish-portion').textContent = item.portion;
    document.querySelector('#dish-price').textContent = money(item.price);
    dishDialog.showModal();
    document.body.classList.add('modal-open');
  }
  function foodCard(item) {
    const card = element('article', 'catalog-dish');
    const button = element('button', 'catalog-dish-photo');
    button.type = 'button';
    button.setAttribute('aria-label', 'Подробнее: ' + item.name);
    button.append(photoNode(item));
    button.addEventListener('click', () => showDish(item));
    const title = element('h3');
    const titleButton = element('button', '', item.name);
    titleButton.type = 'button';
    titleButton.addEventListener('click', () => showDish(item));
    title.append(titleButton);
    card.append(button, title);
    if (item.description) card.append(element('p', 'catalog-description', item.description));
    const line = element('div', 'catalog-price');
    line.append(element('strong', '', money(item.price)), element('span', '', item.portion));
    card.append(line);
    return card;
  }
  function drinkRow(item) {
    const row = element('article', 'bar-menu-row');
    const copy = element('div');
    copy.append(element('h3', '', item.name));
    if (item.description) copy.append(element('p', '', item.description));
    const prices = element('div', 'bar-menu-prices');
    if (item.variants.length) {
      const options = [{ portion: item.portion, price: item.price }, ...item.variants];
      const seen = new Set();
      options.forEach(variant => {
        const key = String(variant.portion) + ':' + String(variant.price);
        if (seen.has(key)) return;
        seen.add(key);
        const line = element('span');
        line.append(element('small', '', variant.portion || variant.volume || ''), element('b', '', money(variant.price)));
        prices.append(line);
      });
    } else {
      const line = element('span');
      line.append(element('small', '', item.portion), element('b', '', money(item.price)));
      prices.append(line);
    }
    row.append(copy, prices);
    return row;
  }
  function selectCategory(value) {
    category = value;
    search.value = '';
    categories.querySelectorAll('button').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.category === value)));
    renderCatalog();
    scrollToControls();
  }
  function renderCategories() {
    categories.replaceChildren();
    (kind === 'food' ? foodFilters : barFilters).forEach(([value, label]) => {
      const button = element('button', '', label);
      button.type = 'button';
      button.dataset.category = value;
      button.setAttribute('aria-pressed', String(category === value));
      button.addEventListener('click', () => selectCategory(value));
      categories.append(button);
    });
  }
  function scrollToControls() {
    const toolbar = document.querySelector('.catalog-toolbar');
    const top = toolbar.getBoundingClientRect().top + window.scrollY;
    if (window.scrollY > top + 30) window.scrollTo({ top: Math.max(0, top - 8), behavior: 'instant' });
  }
  function renderCatalog() {
    const query = normalize(search.value.trim());
    const words = query.split(/\s+/).filter(Boolean);
    const filtered = data.items.filter(item => {
      if (words.length) {
        let keywords = '';
        const text = normalize(item.name + ' ' + item.description);
        if (text.includes('кур')) keywords += ' курица chicken ';
        if (text.includes('кревет')) keywords += ' креветка креветки shrimp ';
        if (text.includes('утин')) keywords += ' утка duck ';
        if (text.includes('говя')) keywords += ' говядина beef ';
        if (text.includes('свин')) keywords += ' свинина pork ';
        if (text.includes('рамен')) keywords += ' ramen ';
        const haystack = normalize(item.name + ' ' + item.description + ' ' + item.category + keywords);
        return words.every(word => haystack.includes(word));
      }
      if (item.food !== (kind === 'food')) return false;
      return category === 'all' || (item.food ? item.category === category : barGroup(item) === category);
    });
    clear.hidden = !query;
    const filterTitle = (kind === 'food' ? foodFilters : barFilters).find(([value]) => value === category)?.[1] || '';
    document.querySelector('#catalog-section-title').textContent = query ? 'Вот что нашлось' : filterTitle;
    document.querySelector('#menu-results').textContent = positionCount(filtered.length);
    document.querySelector('#catalog-empty').hidden = filtered.length > 0;
    results.replaceChildren();
    if (words.length) {
      const food = filtered.filter(item => item.food);
      const drinks = filtered.filter(item => !item.food);
      if (food.length) {
        const section = element('section', 'food-menu-group');
        const grid = element('div', 'catalog-food-grid');
        food.forEach(item => grid.append(foodCard(item)));
        section.append(element('h2', 'catalog-group-title', 'Кухня'), grid);
        results.append(section);
      }
      if (drinks.length) {
        const section = element('section', 'bar-menu-group');
        const list = element('div', 'bar-menu-list');
        drinks.forEach(item => list.append(drinkRow(item)));
        section.append(element('h2', 'catalog-group-title', 'Напитки'), list);
        results.append(section);
      }
      rendered = true;
      return;
    }
    const grouped = new Map();
    filtered.forEach(item => {
      if (!grouped.has(item.category)) grouped.set(item.category, []);
      grouped.get(item.category).push(item);
    });
    grouped.forEach((items, groupName) => {
      const group = element('section', items[0].food ? 'food-menu-group' : 'bar-menu-group');
      const title = element('h2', 'catalog-group-title', groupName === 'Оцунами' ? 'Рис и лапша' : groupName);
      const list = element('div', items[0].food ? 'catalog-food-grid' : 'bar-menu-list');
      items.forEach(item => list.append(item.food ? foodCard(item) : drinkRow(item)));
      group.append(title, list);
      results.append(group);
    });
    rendered = true;
  }
  function renderAtlas() {
    document.querySelectorAll('[data-menu-atlas]').forEach(atlas => {
      data.pages.forEach((page, index) => {
        const button = element('button', 'atlas-page atlas-page-' + (index % 5));
        button.type = 'button';
        button.dataset.art = String(index);
        button.setAttribute('aria-label', 'Открыть лист: ' + page.title);
        const image = document.createElement('img');
        image.src = asset(page.src);
        image.alt = page.title + (data.archive ? ' — архив оригинального меню Teburasi' : ' — рисованное меню Чайханы Базилик');
        image.width = page.width;
        image.height = page.height;
        image.loading = 'lazy';
        image.decoding = 'async';
        const caption = element('span', 'atlas-caption');
        const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        icon.setAttribute('viewBox', '0 0 24 24');
        icon.setAttribute('class', 'ui-icon');
        icon.setAttribute('aria-hidden', 'true');
        const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        use.setAttribute('href', '#ui-arrow');
        icon.append(use);
        caption.append(element('i', '', String(index + 1).padStart(2, '0')), element('span', '', page.title), icon);
        button.append(image, caption);
        atlas.append(button);
      });
    });
  }
  function setMode(value) {
    mode = value;
    document.querySelectorAll('[data-full-mode]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.fullMode === mode)));
    document.querySelector('#catalog-photo-view').hidden = mode !== 'photos';
    document.querySelector('#catalog-art-view').hidden = mode !== 'drawings';
  }
  function renderRoute() {
    const open = location.hash.startsWith('#menu/all');
    const changed = open !== !page.hidden;
    if (open && changed) {
      landingScroll = window.scrollY;
      document.documentElement.classList.add('menu-route');
    }
    landing.hidden = open;
    page.hidden = !open;
    document.body.classList.toggle('catalog-open', open);
    document.title = open ? 'Меню — Чайхана Базилик' : initialTitle;
    if (open) {
      if (!rendered) { renderCategories(); renderCatalog(); }
      if (changed) {
        window.scrollTo({ top: 0, behavior: 'instant' });
        document.querySelector('#catalog-title').focus({ preventScroll: true });
      }
    } else if (changed) {
      window.scrollTo({ top: landingScroll, behavior: 'instant' });
      const heading = document.querySelector(location.hash === '#top' ? '#hero-title' : '#menu-title');
      heading.focus({ preventScroll: true });
      requestAnimationFrame(() => document.documentElement.classList.remove('menu-route'));
    }
  }
  function backToBar() {
    landingScroll = 0;
    history.replaceState(null, '', '#top');
    renderRoute();
  }
  document.addEventListener('click', event => {
    const open = event.target.closest('[data-open-menu]');
    if (open) {
      event.preventDefault();
      history.pushState({ teburasiMenu: true }, '', '#menu/all');
      renderRoute();
    }
    const back = event.target.closest('[data-menu-back]');
    if (back) { event.preventDefault(); backToBar(); }
    const art = event.target.closest('[data-art]');
    if (art) window.TeburasiGallery.open(Number(art.dataset.art), true);
  });
  document.querySelectorAll('[data-menu-kind]').forEach(button => button.addEventListener('click', () => {
    kind = button.dataset.menuKind;
    category = 'all';
    search.value = '';
    document.querySelectorAll('[data-menu-kind]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    renderCategories();
    renderCatalog();
    scrollToControls();
  }));
  document.querySelectorAll('[data-full-mode]').forEach(button => button.addEventListener('click', () => setMode(button.dataset.fullMode)));
  search.addEventListener('input', () => {
    category = 'all';
    renderCategories();
    renderCatalog();
  });
  function resetSearch() { search.value = ''; category = 'all'; renderCategories(); renderCatalog(); search.focus(); }
  clear.addEventListener('click', resetSearch);
  document.querySelector('#reset-menu-search').addEventListener('click', resetSearch);
  document.querySelector('.skip-link').addEventListener('click', event => {
    if (page.hidden) return;
    event.preventDefault();
    document.querySelector('#catalog-title').focus();
  });
  window.addEventListener('popstate', renderRoute);
  document.querySelectorAll('[data-dish]').forEach(button => button.addEventListener('click', () => {
    const item = data.items.find(dish => dish.id === button.dataset.dish);
    if (item) showDish(item);
  }));
  window.addEventListener('hashchange', renderRoute);
  renderAtlas();
  renderRoute();
})();
