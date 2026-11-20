(function(){
  var q=document.getElementById('q'),au=document.getElementById('author'),chips=[].slice.call(document.querySelectorAll('.chip'));
  var browse=document.getElementById('browse'),results=document.getElementById('results'),list=document.getElementById('results-list'),status=document.getElementById('status');
  // one canonical card per tip (topic sections), plus videos
  var cards=[].slice.call(document.querySelectorAll('section.topic .tip, section.videos .video'));
  var active=null;
  function params(){var p=new URLSearchParams(location.search);if(p.get('q'))q.value=p.get('q');if(p.get('author'))au.value=p.get('author');if(p.get('topic'))active=p.get('topic');}
  function sync(){var p=new URLSearchParams();if(q.value)p.set('q',q.value);if(au.value)p.set('author',au.value);if(active)p.set('topic',active);var s=p.toString();history.replaceState(null,'',s?'?'+s+location.hash:location.pathname+location.hash);}
  function run(){
    var terms=q.value.toLowerCase().trim().split(/\s+/).filter(Boolean),a=au.value;
    chips.forEach(function(c){c.setAttribute('aria-pressed',c.dataset.topic===active?'true':'false')});
    if(!terms.length&&!a&&!active){results.hidden=true;browse.hidden=false;status.textContent='';list.innerHTML='';sync();return;}
    var hits=cards.filter(function(c){
      if(a&&c.dataset.author!==a)return false;
      if(active&&c.dataset.topic!==active)return false;
      var s=c.dataset.search;return terms.every(function(t){return s.indexOf(t)>=0});
    });
    list.innerHTML='';hits.forEach(function(c){var n=c.cloneNode(true);n.removeAttribute('id');list.appendChild(n)});
    results.hidden=false;browse.hidden=true;
    status.textContent=hits.length+' match'+(hits.length===1?'':'es')+(hits.length?'':'. Try fewer words or clear a filter.');
    sync();
  }
  chips.forEach(function(c){c.addEventListener('click',function(){active=active===c.dataset.topic?null:c.dataset.topic;run()})});
  q.addEventListener('input',run);au.addEventListener('change',run);
  document.addEventListener('keydown',function(ev){if(ev.key==='/'&&document.activeElement!==q){ev.preventDefault();q.focus()}if(ev.key==='Escape'&&document.activeElement===q){q.value='';run()}});
  params();run();
})();
