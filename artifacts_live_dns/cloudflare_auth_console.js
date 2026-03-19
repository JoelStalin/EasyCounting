(() => {
  const nodes = [...document.querySelectorAll('*')];
  const exact = nodes.find(e => e.innerText && e.innerText.trim() === 'getupsoft.com.do');
  if (!exact) return 'notfound';
  let p = exact;
  for (let i = 0; i < 6 && p; i += 1, p = p.parentElement) {
    try { p.click(); } catch (e) {}
  }
  return 'clicked';
})()