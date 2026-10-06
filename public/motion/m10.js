(() => {
  const STORAGE_KEY="isDarkMode",EVENT_NAME="theme:changed";
  const $=(sel,root=document)=>Array.from(root.querySelectorAll(sel));
  const isCheckbox=el=>el.matches('input[type="checkbox"]');
  const getToggles=()=>$('[data-theme-toggle]');
  const setUI=dark=>getToggles().forEach(el=>{
    if(isCheckbox(el)) el.checked=dark;
    el.setAttribute('aria-pressed',String(dark));
    el.setAttribute('data-theme-state',dark?'dark':'light');
  });
  const applyTheme=(darkOn,emit=true)=>{
    document.body.classList.toggle('dark',darkOn);
    try{localStorage.setItem(STORAGE_KEY,String(darkOn))}catch{}
    setUI(darkOn);
    if(emit&&typeof window!=='undefined') window.dispatchEvent(new CustomEvent(EVENT_NAME,{detail:darkOn}));
  };
  const readInitial=()=>{
    try{const stored=localStorage.getItem(STORAGE_KEY);if(stored==='true'||stored==='false')return stored==='true'}catch{}
    return true;
  };
  const currentIsDark=()=>document.body.classList.contains('dark');
  const onToggle=e=>{
    const el=e.currentTarget,next=isCheckbox(el)?el.checked:!currentIsDark();
    applyTheme(next);
  };
  const bindAll=()=>getToggles().forEach(el=>{
    if(el.__themeBound)return;
    el.__themeBound=true;
    el.addEventListener(isCheckbox(el)?'change':'click',onToggle);
  });
  const init=()=>{
    applyTheme(readInitial(),false);
    bindAll();
    window.addEventListener(EVENT_NAME,e=>{if(e&&typeof e.detail==='boolean')applyTheme(e.detail,false)});
    window.addEventListener('storage',e=>{if(e.key===STORAGE_KEY&&e.newValue!=null)applyTheme(e.newValue==='true',false)});
    new MutationObserver(()=>bindAll()).observe(document.body,{subtree:true,childList:true});
  };
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init();
})();