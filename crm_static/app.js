(function () {
  'use strict';

  // ── Path prefix detection ─────────────────────────────────
  var pathPrefix = '';
  if (window.location.pathname.indexOf('/crm') === 0) pathPrefix = '/crm';

  // ── Load inventory and render ──────────────────────────────
  var grid = document.getElementById('vehicle-grid');
  var inventory = [];

  fetch(pathPrefix + '/static/inventory.json')
    .then(function (r) { return r.json(); })
    .catch(function () {
      return fetch(pathPrefix + '/data/inventory.json').then(function (r) { return r.json(); });
    })
    .then(function (data) {
      inventory = data.inventory || [];
      renderVehicles(inventory);
    })
    .catch(function () {
      if (grid) grid.innerHTML = '<p style="text-align:center;color:#999;padding:2rem;">Unable to load inventory.</p>';
    });

  function getDetailUrl(v) {
    // Use internal /crm/vehicle/<slug> page
    if (v.slug) return pathPrefix + '/vehicle/' + v.slug;
    return v.external_url || '#';
  }

  function getHeroImage(v) {
    if (v.hero_image) return v.hero_image;
    // Fallback to static local images
    var model = v.model || '';
    if (model.indexOf('LC79') >= 0 || model.indexOf('LC76') >= 0 || model.indexOf('LC71') >= 0) return pathPrefix + '/static/img/lc79.png';
    if (model.indexOf('LC300') >= 0 || model.indexOf('4Runner') >= 0 || model.indexOf('GX') >= 0) return pathPrefix + '/static/img/lc300.png';
    if (model.indexOf('Prado') >= 0) return pathPrefix + '/static/img/prado.png';
    if (model.indexOf('Hilux') >= 0 || model.indexOf('BT-50') >= 0 || model.indexOf('D-MAX') >= 0) return pathPrefix + '/static/img/hilux.png';
    if (model.indexOf('Defender') >= 0) return pathPrefix + '/static/img/defender.png';
    if (model.indexOf('Wrangler') >= 0) return pathPrefix + '/static/img/wrangler.png';
    return pathPrefix + '/static/img/lc79.png';
  }

  function renderVehicles(vehicles) {
    if (!grid) return;
    grid.innerHTML = '';
    vehicles.forEach(function (v) {
      var card = document.createElement('article');
      card.className = 'vehicle-card';
      card.setAttribute('data-make', v.make || '');

      var imgSrc = getHeroImage(v);
      var detailUrl = getDetailUrl(v);
      var waMsg = encodeURIComponent(
        'Hi, I am interested in the ' + v.year + ' ' + v.make + ' ' + v.model + ' ' + (v.variant || '') + '. Is it still available?'
      );

      var statusBadge = '';
      if (v.status === 'sold') {
        statusBadge = '<span class="vehicle-badge sold">SOLD</span>';
      }

      card.innerHTML =
        '<a href="' + detailUrl + '" class="vehicle-card__img-wrap">' +
          '<img class="vehicle-card__img" src="' + imgSrc + '" alt="' + v.year + ' ' + v.make + ' ' + v.model + '" loading="lazy" width="600" height="220" />' +
          statusBadge +
        '</a>' +
        '<div class="vehicle-card__body">' +
          '<span class="vehicle-card__year">' + v.year + '</span>' +
          '<h3 class="vehicle-card__title"><a href="' + detailUrl + '" style="color:inherit;text-decoration:none">' + v.make + ' ' + v.model + '</a></h3>' +
          '<p class="vehicle-card__variant">' + (v.variant || '') + '</p>' +
          (v.color ? '<p class="vehicle-card__meta"><span>🎨 ' + v.color + '</span>' + (v.transmission ? ' · <span>⚙️ ' + v.transmission + '</span>' : '') + '</p>' : '') +
          '<div class="vehicle-card__actions">' +
            '<a href="' + detailUrl + '" class="btn btn-outline">Details</a>' +
            '<a href="https://api.whatsapp.com/send/?phone=50684527966&text=' + waMsg + '&type=phone_number&app_absent=0" class="btn btn-wa" target="_blank">Inquire</a>' +
          '</div>' +
        '</div>';

      grid.appendChild(card);
    });
  }

  // ── Filter buttons ─────────────────────────────────────────
  var filterBar = document.getElementById('filter-bar');
  if (filterBar) {
    filterBar.addEventListener('click', function (e) {
      var btn = e.target.closest('.filter-btn');
      if (!btn) return;
      filterBar.querySelectorAll('.filter-btn').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      var filter = btn.getAttribute('data-filter');
      if (filter === 'all') {
        renderVehicles(inventory);
      } else if (filter === 'Other') {
        renderVehicles(inventory.filter(function (v) {
          return v.make !== 'Toyota' && v.make !== 'Land Rover' && v.make !== 'Jeep';
        }));
      } else {
        renderVehicles(inventory.filter(function (v) { return v.make === filter; }));
      }
    });
  }

  // ── Mobile nav toggle ──────────────────────────────────────
  var toggle = document.getElementById('nav-toggle');
  var nav = document.getElementById('main-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () { nav.classList.toggle('is-open'); });
    nav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { nav.classList.remove('is-open'); });
    });
  }

})();
