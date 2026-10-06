(function(){
  const el=document.getElementById("progress");
  function update(){
    let scrolled=Math.min(Math.max((window.scrollY/(document.documentElement.scrollHeight-window.innerHeight))*100,0),100);
    el.textContent=Math.round(scrolled)+"%";
    requestAnimationFrame(update);
  }
  update();
})();