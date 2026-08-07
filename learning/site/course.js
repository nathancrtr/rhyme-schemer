(function(){
  var root=document.documentElement, btn=document.getElementById("theme-toggle");
  if(btn) btn.addEventListener("click",function(){
    var dark=root.dataset.theme
      ? root.dataset.theme==="dark"
      : matchMedia("(prefers-color-scheme:dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try{localStorage.setItem("rs-theme",root.dataset.theme);}catch(e){}
  });
  var links=[].slice.call(document.querySelectorAll(".rail a"));
  if(!links.length||!window.IntersectionObserver) return;
  var byId={};
  links.forEach(function(a){ byId[a.getAttribute("href").slice(1)]=a; });
  var visible={};
  var obs=new IntersectionObserver(function(entries){
    entries.forEach(function(e){ visible[e.target.id]=e.isIntersecting; });
    var current=null;
    Object.keys(byId).forEach(function(id){ if(visible[id]&&!current) current=id; });
    links.forEach(function(a){ a.classList.remove("on"); });
    if(current&&byId[current]) byId[current].classList.add("on");
  },{rootMargin:"-88px 0px -70% 0px"});
  Object.keys(byId).forEach(function(id){
    var el=document.getElementById(id); if(el) obs.observe(el);
  });
})();
