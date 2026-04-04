document.addEventListener('DOMContentLoaded', () => {
  const tabs = Array.from(document.querySelectorAll('.tab'));
  const panels = Array.from(document.querySelectorAll('[id^="panel-"]'));

  function getPanel(id){
    return document.getElementById('panel-' + id);
  }

  function show(id){
    // Masquer tous les panneaux
    panels.forEach(p => p.classList.remove('show'));

    // Trouver le panneau demandé
    let panel = getPanel(id);
    if (!panel) {
      // si id inconnu, tomber sur le 1er panneau existant
      panel = panels[0];
      if (!panel) return; // aucun panneau sur la page
      id = panel.id.replace('panel-','');
    }
    panel.classList.add('show');

    // Tabs actif/inactif (ne pas planter si mismatch)
    tabs.forEach(t => {
      const active = (t.dataset.tab === id);
      t.classList.toggle('active', active);
      t.setAttribute('aria-selected', active ? 'true' : 'false');
    });

    // Mettre à jour le hash
    if (location.hash.replace('#','') !== id) {
      history.replaceState(null, '', '#' + id);
    }
  }

  // Clics onglets
  tabs.forEach(t => t.addEventListener('click', () => show(t.dataset.tab)));

  // Ouverture initiale
  const initial = location.hash ? location.hash.replace('#','') : (tabs[0]?.dataset.tab || '');
  show(initial);
});
