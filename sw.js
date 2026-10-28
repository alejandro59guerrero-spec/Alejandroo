// Mis Metas · Campo: guarda la app en el iPhone para abrirla sin señal
const V='campo-d925e988df';
const FILES=['./','./index.html','./manifest.webmanifest','./icon-180.png','./icon-192.png','./icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  const r=e.request; if(r.method!=='GET')return;
  const u=new URL(r.url); if(u.origin!==location.origin)return;
  const nav=r.mode==='navigate';
  e.respondWith(caches.open(V).then(async c=>{
    const hit=await c.match(nav?'./index.html':r,{ignoreSearch:true});
    const net=fetch(r).then(res=>{if(res&&res.ok&&!nav)c.put(r,res.clone());return res}).catch(()=>null);
    if(hit){e.waitUntil(net);return hit}
    return (await net)||new Response('Sin conexión',{status:503});
  }));
});
