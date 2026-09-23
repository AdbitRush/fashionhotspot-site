/* AllyFind — the ONE theme initialisation path, for every page family
   (homepage, guides index, guide articles, static pages). Linked from <head> as a
   small blocking script so the theme is applied BEFORE first paint; a page never
   flashes dark and then turns light (or the reverse).

   Rules
   - A saved choice ("light" or "dark" under localStorage key fh-theme) always wins.
   - With no saved choice the page is LIGHT. The operating-system colour scheme is
     deliberately NOT consulted: a visitor with a dark OS still gets light until
     they press the toggle.
   - Both markers are set so both stylesheets' selectors work from one source of
     truth: <html data-theme="light|dark"> and, for dark, <html class="dark">.
   - Toggle buttons (.themetog on guides/static pages, #theme-btn on the
     homepage) are kept in sync: aria-pressed, and the homepage glyph. */
(function () {
  var KEY = 'fh-theme', d = document.documentElement;

  function saved() {
    try { var t = localStorage.getItem(KEY); return t === 'dark' || t === 'light' ? t : null; } catch (e) { return null; }
  }
  function current() { return d.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'; }

  function sync(t) {
    var dark = t === 'dark';
    var btns = document.querySelectorAll('.themetog, #theme-btn');
    for (var i = 0; i < btns.length; i++) {
      btns[i].setAttribute('aria-pressed', dark ? 'true' : 'false');
      if (btns[i].id === 'theme-btn') btns[i].textContent = dark ? '🌙' : '☀️';
    }
  }
  function apply(t) {
    d.setAttribute('data-theme', t);
    if (t === 'dark') d.classList.add('dark'); else d.classList.remove('dark');
    sync(t);
  }
  function set(t) {
    apply(t);
    try { localStorage.setItem(KEY, t); } catch (e) {}
  }
  function toggle() { set(current() === 'dark' ? 'light' : 'dark'); }

  apply(saved() || 'light');

  window.fhTheme = { get: current, set: set, toggle: toggle };
  window.fhToggleTheme = toggle;   // guides + static pages
  window.toggleTheme = toggle;     // homepage (existing onclick)

  document.addEventListener('DOMContentLoaded', function () { sync(current()); });
  // Another tab changed the choice: follow it.
  window.addEventListener('storage', function (e) {
    if (e.key === KEY || e.key === null) apply(saved() || 'light');
  });
})();
