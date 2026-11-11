      const W=(k,i)=>SEG[k].w[i].s-S0, WE=(k,i)=>SEG[k].w[i].e-S0, LS=k=>SEG[k].s-S0, LE=k=>SEG[k].e-S0;
      const blurIn=(tl,sel,t,st=0.07,d=0.22)=>tl.fromTo(sel,{opacity:0,filter:"blur(12px)"},{opacity:1,filter:"blur(0px)",duration:d,stagger:st,ease:"power2.out"},t);
      const rise=(tl,sel,t,o={})=>tl.fromTo(sel,{opacity:0,scale:0.95,x:o.x||0,y:o.y===undefined?46:o.y,rotation:o.r||0},{opacity:1,scale:1,x:0,y:0,rotation:o.r1||0,duration:o.d||0.5,stagger:o.st||0,ease:o.ease||"expo.out"},t);
      const rng=(a=>()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296})(SEED);
